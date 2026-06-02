from django.core.management.base import BaseCommand

from character.seeds import (
    ADMIN_PASSWORD, ADMIN_USERNAME, DRUID_NAME, FIGHTER_NAME, RANGER_NAME,
    WIZARD_NAME, seed_all,
)


class Command(BaseCommand):
    help = (
        'Popula o banco com a conta admin e fichas de exemplo '
        '(Guerreiro, Mago, Druida e Ranger). Idempotente: recria as fichas '
        'de exemplo a cada execução.'
    )

    def handle(self, *args, **options):
        result = seed_all()
        self.stdout.write(self.style.SUCCESS('Seed concluído.'))
        self.stdout.write(f"  Admin:     {ADMIN_USERNAME} / {ADMIN_PASSWORD} (superusuário — só para uso local)")
        self.stdout.write(f"  Guerreiro: {FIGHTER_NAME} (pk={result['fighter'].pk})")
        self.stdout.write(f"  Mago:      {WIZARD_NAME} (pk={result['wizard'].pk})")
        self.stdout.write(f"  Druida:    {DRUID_NAME} (pk={result['druid'].pk})")
        self.stdout.write(f"  Ranger:    {RANGER_NAME} (pk={result['ranger'].pk})")
