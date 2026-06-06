import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sdr.models import SDR_Monster


HEADING_RE = re.compile(r'^##\s+(.+?)\s*$')
EMPTY_FIELDS = ('special_abilities', 'attack', 'special_attacks')


@dataclass
class MarkdownFamily:
    name: str
    body: str


@dataclass
class FamilyAudit:
    name: str
    body: str
    status: str
    matches: list


def normalize(value):
    value = unicodedata.normalize('NFKD', value or '')
    value = ''.join(char for char in value if not unicodedata.combining(char))
    value = value.casefold()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def monster_is_empty(monster, field_name):
    value = getattr(monster, field_name)
    return value is None or str(value).strip() == ''


def extract_families(markdown):
    families = []
    current_name = None
    current_body = []
    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            if current_name is not None:
                families.append(MarkdownFamily(current_name, '\n'.join(current_body).strip()))
            current_name = match.group(1).strip()
            current_body = []
        elif current_name is not None:
            current_body.append(line)
    if current_name is not None:
        families.append(MarkdownFamily(current_name, '\n'.join(current_body).strip()))
    return families


def audit_families(families, monsters, family_justifications=None):
    family_justifications = family_justifications or {}
    audits = []
    for family in families:
        normalized_family = normalize(family.name)
        family_matches = [
            monster for monster in monsters
            if normalize(monster.family) == normalized_family
        ]
        if family_matches:
            audits.append(FamilyAudit(family.name, family.body, 'OK', family_matches))
            continue
        if normalized_family in family_justifications:
            audits.append(FamilyAudit(family.name, family.body, 'JUSTIFICADO', []))
            continue

        exact_name_matches = [
            monster for monster in monsters
            if normalize(monster.name) == normalized_family
        ]
        if exact_name_matches:
            audits.append(FamilyAudit(family.name, family.body, 'OK', exact_name_matches))
            continue

        name_matches = [
            monster for monster in monsters
            if normalized_family and normalized_family in normalize(monster.name)
        ]
        if name_matches:
            audits.append(FamilyAudit(family.name, family.body, 'REVISAR', name_matches))
        else:
            audits.append(FamilyAudit(family.name, family.body, 'FALTA', []))
    return audits


def load_justifications(path):
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    justifications = {}
    for item in data:
        monster_id = item.get('id')
        for field_name, reason in (item.get('fields') or {}).items():
            justifications[(monster_id, field_name)] = reason
    return justifications


def load_family_justifications(path):
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    return {
        normalize(item.get('family')): item.get('reason', '')
        for item in data
        if item.get('family')
    }


def gaps_for_monsters(monsters, justifications=None):
    justifications = justifications or {}
    gaps = []
    justified = []
    seen = set()
    for monster in monsters:
        if monster.pk in seen:
            continue
        seen.add(monster.pk)
        missing = []
        for field in EMPTY_FIELDS:
            if not monster_is_empty(monster, field):
                continue
            reason = justifications.get((monster.pk, field))
            if reason:
                justified.append((monster, field, reason))
            else:
                missing.append(field)
        if missing:
            gaps.append((monster, missing))
    return gaps, justified


def render_report(letter, source_path, audits, gaps, justified):
    lines = [
        f'# Cobertura de monstros - {letter}',
        '',
        f'Fonte: `{source_path}`',
        '',
        '## Familias',
        '',
        '| Familia | Status | Linhas no banco |',
        '|---------|--------|-----------------|',
    ]

    for audit in audits:
        names = ', '.join(f'[{monster.pk}] {monster.name}' for monster in audit.matches)
        lines.append(f'| {audit.name} | {audit.status} | {names or "-"} |')

    lines.extend([
        '',
        '## Lacunas de campos',
        '',
    ])

    if gaps:
        lines.extend([
            '| ID | Monstro | Campos vazios |',
            '|----|---------|---------------|',
        ])
        for monster, missing in gaps:
            lines.append(f'| {monster.pk} | {monster.name} | {", ".join(missing)} |')
    else:
        lines.append('Nenhuma lacuna encontrada nos monstros cobertos por esta letra.')

    if justified:
        lines.extend([
            '',
            '## Campos vazios justificados',
            '',
            '| ID | Monstro | Campo | Justificativa |',
            '|----|---------|-------|---------------|',
        ])
        for monster, field_name, reason in justified:
            lines.append(f'| {monster.pk} | {monster.name} | {field_name} | {reason} |')

    review_items = [
        audit for audit in audits
        if audit.status in {'FALTA', 'REVISAR', 'JUSTIFICADO'}
    ]
    if review_items:
        lines.extend([
            '',
            '## Trechos da fonte para revisar',
            '',
        ])
        for audit in review_items:
            excerpt = audit.body[:1200].strip() or '(sem corpo abaixo do cabecalho)'
            lines.extend([
                f'### {audit.name} - {audit.status}',
                '',
                '```markdown',
                excerpt,
                '```',
                '',
            ])

    lines.append('')
    return '\n'.join(lines)


class Command(BaseCommand):
    help = 'Audita cobertura dos monstros do SRD contra .data/Monsters/*.md.'

    def add_arguments(self, parser):
        default_data_dir = Path(settings.BASE_DIR).parent / '.data' / 'Monsters'
        default_output_dir = Path(settings.BASE_DIR).parent / 'tmp'
        default_justifications = Path(settings.BASE_DIR) / 'sdr' / 'data' / 'monster_field_justifications.json'
        default_family_justifications = Path(settings.BASE_DIR) / 'sdr' / 'data' / 'monster_family_justifications.json'
        parser.add_argument('--db', default='sdr', help='Alias do banco SDR.')
        parser.add_argument('--data-dir', default=str(default_data_dir), help='Diretorio com os markdowns de monstros.')
        parser.add_argument('--output-dir', default=str(default_output_dir), help='Diretorio para relatorios gerados.')
        parser.add_argument(
            '--justifications-file',
            default=str(default_justifications),
            help='JSON com justificativas para campos vazios aceitos.',
        )
        parser.add_argument(
            '--family-justifications-file',
            default=str(default_family_justifications),
            help='JSON com justificativas para familias sem linha propria no banco.',
        )
        parser.add_argument('--letter', help='Audita apenas uma letra, por exemplo A.')

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        output_dir = Path(options['output_dir'])
        db_alias = options['db']
        justifications_file = Path(options['justifications_file']) if options.get('justifications_file') else None
        family_justifications_file = (
            Path(options['family_justifications_file'])
            if options.get('family_justifications_file')
            else None
        )

        if not data_dir.exists():
            raise CommandError(f'Diretorio nao encontrado: {data_dir}')

        letters = [options['letter'].upper()] if options.get('letter') else None
        markdowns = sorted(data_dir.glob('3.5 Monsters - *.md'))
        if letters:
            markdowns = [
                path for path in markdowns
                if path.stem.removeprefix('3.5 Monsters - ').upper() in letters
            ]
        if not markdowns:
            raise CommandError('Nenhum markdown de monstros encontrado para auditar.')

        output_dir.mkdir(parents=True, exist_ok=True)
        monsters = list(SDR_Monster.objects.using(db_alias).all().order_by('id'))
        justifications = load_justifications(justifications_file)
        family_justifications = load_family_justifications(family_justifications_file)

        total_families = total_missing = total_review = total_family_justified = 0
        total_gaps = total_justified = 0
        for markdown_path in markdowns:
            letter = markdown_path.stem.removeprefix('3.5 Monsters - ')
            families = extract_families(markdown_path.read_text(encoding='utf-8'))
            audits = audit_families(families, monsters, family_justifications)
            matched_monsters = [monster for audit in audits for monster in audit.matches]
            gaps, justified = gaps_for_monsters(matched_monsters, justifications)

            report = render_report(letter, markdown_path, audits, gaps, justified)
            report_path = output_dir / f'monster_coverage_{letter}.md'
            report_path.write_text(report, encoding='utf-8')

            missing = sum(1 for audit in audits if audit.status == 'FALTA')
            review = sum(1 for audit in audits if audit.status == 'REVISAR')
            family_justified = sum(1 for audit in audits if audit.status == 'JUSTIFICADO')
            total_families += len(audits)
            total_missing += missing
            total_review += review
            total_family_justified += family_justified
            total_gaps += len(gaps)
            total_justified += len(justified)

            self.stdout.write(
                f'{letter}: familias={len(audits)} falta={missing} revisar={review} '
                f'familias_justificadas={family_justified} lacunas={len(gaps)} '
                f'justificadas={len(justified)} relatorio={report_path}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Auditoria concluida: familias={total_families} falta={total_missing} '
                f'revisar={total_review} familias_justificadas={total_family_justified} '
                f'lacunas={total_gaps} justificadas={total_justified}'
            )
        )
