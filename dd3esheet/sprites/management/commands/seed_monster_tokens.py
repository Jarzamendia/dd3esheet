from django.core.management.base import BaseCommand

from sprites.seeds import seed_monster_tokens


class Command(BaseCommand):
    help = 'Cria/reutiliza um SpriteAsset por monstro do SDR e vincula por id e nome.'

    def handle(self, *args, **options):
        summary = seed_monster_tokens()
        self.stdout.write(self.style.SUCCESS(
            f"Monstros: {summary['total']} | "
            f"{summary['created']} criados, {summary['reused']} reutilizados, "
            f"{summary['bound']} vinculos."
        ))
