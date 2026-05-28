from django.core.management.base import BaseCommand

from character.seeds import (
    ADMIN_PASSWORD, ADMIN_USERNAME, FIGHTER_NAME, WIZARD_NAME, seed_all,
)


class Command(BaseCommand):
    help = (
        'Popula o banco com a conta admin e fichas de exemplo '
        '(Guerreiro nível 5 e Mago nível 8). Idempotente: recria as fichas '
        'de exemplo a cada execução.'
    )

    def handle(self, *args, **options):
        result = seed_all()
        self.stdout.write(self.style.SUCCESS('Seed concluído.'))
        self.stdout.write(f"  Admin:     {ADMIN_USERNAME} / {ADMIN_PASSWORD} (superusuário — só para uso local)")
        self.stdout.write(f"  Guerreiro: {FIGHTER_NAME} (pk={result['fighter'].pk})")
        self.stdout.write(f"  Mago:      {WIZARD_NAME} (pk={result['wizard'].pk})")
