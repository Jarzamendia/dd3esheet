from django.core.management.base import BaseCommand

from sprites.seeds import seed_sprites


class Command(BaseCommand):
    help = 'Popula a biblioteca de sprites com placeholders locais e bindings padrao.'

    def handle(self, *args, **options):
        assets = seed_sprites()
        self.stdout.write(self.style.SUCCESS(
            f'Sprites seed concluido: {len(assets)} assets/bindings, sem criar arquivos de imagem.'
        ))
