from django.core.management.base import BaseCommand

from sprites.seeds import seed_sprite_library


class Command(BaseCommand):
    help = 'Cria/atualiza placeholders SpriteAsset dos assets do manifesto.'

    def handle(self, *args, **options):
        summary = seed_sprite_library()
        self.stdout.write(self.style.SUCCESS(
            f"Sprites: {summary['created']} criados, {summary['updated']} atualizados."
        ))
