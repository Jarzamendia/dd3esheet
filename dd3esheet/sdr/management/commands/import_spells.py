import json
import os
from django.core.management.base import BaseCommand
from sdr.models import SDR_Spell
from sdr.lookups import resolve_spell

class Command(BaseCommand):
    help = 'Importa ou traduz magias (spells) em portugues no banco de dados SDR'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'spells_pt.json'),
            help='Caminho do arquivo JSON a ser importado'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Arquivo nao encontrado: {file_path}'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                spells_data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao ler arquivo JSON: {str(e)}'))
            return

        created_count = 0
        updated_count = 0

        for item in spells_data:
            name = item.get('name')
            altname = item.get('altname', '')
            if not name:
                continue

            # Prioriza match por altname (nome original em inglês),
            # cai para name (português) — encapsulado em resolve_spell.
            existing = resolve_spell(altname) or resolve_spell(name)

            data = {
                'name': name,
                'altname': altname,
                'school': item.get('school', ''),
                'subschool': item.get('subschool', ''),
                'descriptor': item.get('descriptor', ''),
                'spellcraft_dc': item.get('spellcraft_dc', ''),
                'level': item.get('level', ''),
                'components': item.get('components', ''),
                'casting_time': item.get('casting_time', ''),
                'range': item.get('range', ''),
                'target': item.get('target', ''),
                'area': item.get('area', ''),
                'effect': item.get('effect', ''),
                'duration': item.get('duration', ''),
                'saving_throw': item.get('saving_throw', ''),
                'spell_resistance': item.get('spell_resistance', ''),
                'short_description': item.get('short_description', ''),
                'description': item.get('description', ''),
                'full_text': item.get('full_text', ''),
                'reference': item.get('reference', 'Livro do Jogador 3.5 (PT)'),
            }

            if existing is not None:
                # Atualiza/Traduz in-place
                for key, val in data.items():
                    setattr(existing, key, val)
                existing.save(using='sdr')
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Traduzida magia: {altname or name} -> {name}'))
            else:
                # Cria uma nova magia
                spell = SDR_Spell(**data)
                spell.save(using='sdr')
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Criada magia: {name}'))

        self.stdout.write(self.style.SUCCESS(
            f'Importacao de magias concluida com sucesso! Criadas: {created_count}, Traduzidas/Atualizadas: {updated_count}'
        ))
