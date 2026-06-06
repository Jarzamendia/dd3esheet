import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sdr.models import SDR_Monster


ALLOWED_FIELDS = {'special_abilities', 'attack', 'special_attacks'}


def is_empty(value):
    return value is None or str(value).strip() == ''


class Command(BaseCommand):
    help = 'Preenche lacunas conhecidas de campos de monstros no banco SDR.'

    def add_arguments(self, parser):
        default_file = Path(settings.BASE_DIR) / 'sdr' / 'data' / 'monster_field_backfills.json'
        parser.add_argument('--db', default='sdr', help='Alias do banco SDR.')
        parser.add_argument('--file', default=str(default_file), help='Arquivo JSON com backfills.')
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que mudaria sem salvar.')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescreve campos ja preenchidos quando o valor for diferente.',
        )

    def handle(self, *args, **options):
        db_alias = options['db']
        file_path = Path(options['file'])
        dry_run = options['dry_run']
        force = options['force']

        if not file_path.exists():
            raise CommandError(f'Arquivo nao encontrado: {file_path}')

        try:
            backfills = json.loads(file_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise CommandError(f'JSON invalido em {file_path}: {exc}') from exc

        updated = skipped = missing = conflicts = 0
        for item in backfills:
            monster_id = item.get('id')
            expected_name = (item.get('name') or '').strip()
            fields = item.get('fields') or {}

            invalid_fields = set(fields) - ALLOWED_FIELDS
            if invalid_fields:
                raise CommandError(
                    f'Campos invalidos para {expected_name or monster_id}: '
                    f'{", ".join(sorted(invalid_fields))}'
                )

            try:
                monster = SDR_Monster.objects.using(db_alias).get(pk=monster_id)
            except SDR_Monster.DoesNotExist:
                missing += 1
                self.stdout.write(self.style.ERROR(f'Nao encontrado: [{monster_id}] {expected_name}'))
                continue

            if expected_name and monster.name != expected_name:
                conflicts += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Nome divergente para [{monster_id}]: esperado "{expected_name}", '
                        f'encontrado "{monster.name}"'
                    )
                )
                continue

            changed_fields = []
            for field_name, value in fields.items():
                current_value = getattr(monster, field_name)
                if current_value == value:
                    skipped += 1
                    continue
                if not is_empty(current_value) and not force:
                    conflicts += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Campo ja preenchido: [{monster.pk}] {monster.name}.{field_name}'
                        )
                    )
                    continue
                setattr(monster, field_name, value)
                changed_fields.append(field_name)

            if not changed_fields:
                continue

            if dry_run:
                skipped += len(changed_fields)
                self.stdout.write(
                    f'DRY-RUN preencheria [{monster.pk}] {monster.name}: {", ".join(changed_fields)}'
                )
                continue

            monster.save(using=db_alias, update_fields=changed_fields)
            updated += len(changed_fields)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Preenchido [{monster.pk}] {monster.name}: {", ".join(changed_fields)}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Backfill concluido: atualizados={updated} pulados={skipped} '
                f'nao_encontrados={missing} conflitos={conflicts}'
            )
        )
