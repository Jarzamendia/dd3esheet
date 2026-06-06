from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from sdr.management.commands.audit_monster_coverage import EMPTY_FIELDS, load_justifications
from sdr.models import SDR_Monster


def is_empty(value):
    return value is None or str(value).strip() == ''


class Command(BaseCommand):
    help = 'Audita lacunas de campos de todos os monstros no banco SDR.'

    def add_arguments(self, parser):
        default_justifications = Path(settings.BASE_DIR) / 'sdr' / 'data' / 'monster_field_justifications.json'
        default_output = Path(settings.BASE_DIR).parent / 'tmp' / 'monster_field_gaps.md'
        parser.add_argument('--db', default='sdr', help='Alias do banco SDR.')
        parser.add_argument(
            '--justifications-file',
            default=str(default_justifications),
            help='JSON com justificativas para campos vazios aceitos.',
        )
        parser.add_argument('--output', default=str(default_output), help='Relatorio Markdown gerado.')

    def handle(self, *args, **options):
        db_alias = options['db']
        output_path = Path(options['output'])
        justifications = load_justifications(Path(options['justifications_file']))

        open_gaps = []
        justified = []
        for monster in SDR_Monster.objects.using(db_alias).all().order_by('id'):
            for field in EMPTY_FIELDS:
                if not is_empty(getattr(monster, field)):
                    continue
                reason = justifications.get((monster.pk, field))
                if reason:
                    justified.append((monster, field, reason))
                else:
                    open_gaps.append((monster, field))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            '# Lacunas de campos de monstros',
            '',
            f'Lacunas abertas: {len(open_gaps)}',
            f'Lacunas justificadas: {len(justified)}',
            '',
            '## Abertas',
            '',
        ]
        if open_gaps:
            lines.extend(['| ID | Monstro | Campo |', '|----|---------|-------|'])
            for monster, field in open_gaps:
                lines.append(f'| {monster.pk} | {monster.name} | {field} |')
        else:
            lines.append('Nenhuma lacuna aberta.')

        lines.extend(['', '## Justificadas', ''])
        if justified:
            lines.extend(['| ID | Monstro | Campo | Justificativa |', '|----|---------|-------|---------------|'])
            for monster, field, reason in justified:
                lines.append(f'| {monster.pk} | {monster.name} | {field} | {reason} |')
        else:
            lines.append('Nenhuma lacuna justificada.')

        output_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        self.stdout.write(
            self.style.SUCCESS(
                f'Auditoria de campos concluida: abertas={len(open_gaps)} '
                f'justificadas={len(justified)} relatorio={output_path}'
            )
        )
