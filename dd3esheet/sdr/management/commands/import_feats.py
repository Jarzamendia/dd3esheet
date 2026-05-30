import json
import os
from django.core.management.base import BaseCommand
from sdr.models import SDR_Feat

class Command(BaseCommand):
    help = 'Importa ou atualiza talentos (feats) em português no banco de dados SDR'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'feats_pt.json'),
            help='Caminho do arquivo JSON a ser importado'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Arquivo nao encontrado: {file_path}'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                feats_data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao ler arquivo JSON: {str(e)}'))
            return

        created_count = 0
        updated_count = 0

        for item in feats_data:
            name = item.get('name')
            if not name:
                continue

            # Tenta buscar pelo nome exato no banco SDR
            feat_qs = SDR_Feat.objects.using('sdr').filter(name__iexact=name)

            data = {
                'type': item.get('type', 'General'),
                'multiple': item.get('multiple', 'No'),
                'stack': item.get('stack', 'No'),
                'choice': item.get('choice', ''),
                'prerequisite': item.get('prerequisite', ''),
                'benefit': item.get('benefit', ''),
                'normal': item.get('normal', ''),
                'special': item.get('special', ''),
                'full_text': item.get('full_text', ''),
                'reference': item.get('reference', 'Livro do Jogador 3.5 (PT)'),
            }

            if feat_qs.exists():
                # Atualiza
                feat = feat_qs.first()
                for key, val in data.items():
                    setattr(feat, key, val)
                feat.save(using='sdr')
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Atualizado talento: {name}'))
            else:
                # Cria um novo
                feat = SDR_Feat(name=name, **data)
                feat.save(using='sdr')
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Criado talento: {name}'))

        self.stdout.write(self.style.SUCCESS(
            f'Importacao concluida com sucesso! Criados: {created_count}, Atualizados: {updated_count}'
        ))
