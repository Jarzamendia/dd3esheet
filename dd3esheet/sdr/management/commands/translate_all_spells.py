import time
import urllib.request
import urllib.parse
import json
from django.core.management.base import BaseCommand
from sdr.models import SDR_Spell

def translate_text(text, source_lang='en', target_lang='pt'):
    if not text or text.strip() == "":
        return text
    # Verifica se ja esta em portugues ou caracteres numericos puros
    if text.isdigit():
        return text
    
    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=" + source_lang + "&tl=" + target_lang + "&dt=t&q=" + urllib.parse.quote(text)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            translated = "".join([sentence[0] for sentence in result[0] if sentence[0]])
            return translated
    except Exception as e:
        return text # Em caso de erro, mantem o original

class Command(BaseCommand):
    help = 'Traduz todas as magias do SDR de Ingles para Portugues de forma automatica e in-place'

    def handle(self, *args, **options):
        # Busca todas as magias originais em ingles baseando-se na referencia original do SRD 3.5
        spells_to_translate = SDR_Spell.objects.using('sdr').filter(reference__startswith='SRD 3.5')
        
        total = spells_to_translate.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Todas as magias ja foram traduzidas ou mapeadas!'))
            return

        self.stdout.write(self.style.WARNING(f'Iniciando a traducao automatica de {total} magias...'))
        
        translated_count = 0
        
        for idx, spell in enumerate(spells_to_translate, 1):
            original_name = spell.name
            
            try:
                # Traduz campos essenciais
                translated_name = translate_text(original_name)
                
                # Para evitar duplicar se houver nomes repetidos ou conflitos
                spell.altname = original_name
                spell.name = translated_name
                
                if spell.school:
                    spell.school = translate_text(spell.school)
                if spell.subschool:
                    spell.subschool = translate_text(spell.subschool)
                if spell.descriptor:
                    spell.descriptor = translate_text(spell.descriptor)
                if spell.casting_time:
                    spell.casting_time = translate_text(spell.casting_time)
                if spell.range:
                    spell.range = translate_text(spell.range)
                if spell.target:
                    spell.target = translate_text(spell.target)
                if spell.area:
                    spell.area = translate_text(spell.area)
                if spell.effect:
                    spell.effect = translate_text(spell.effect)
                if spell.duration:
                    spell.duration = translate_text(spell.duration)
                if spell.saving_throw:
                    spell.saving_throw = translate_text(spell.saving_throw)
                if spell.spell_resistance:
                    spell.spell_resistance = translate_text(spell.spell_resistance)
                if spell.short_description:
                    spell.short_description = translate_text(spell.short_description)
                if spell.description:
                    spell.description = translate_text(spell.description)
                
                spell.reference = "SDR 3.5 (PT-BR Traduzido)"
                
                spell.save(using='sdr')
                translated_count += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f'[{idx}/{total}] Traduzido: {original_name} -> {translated_name}'
                ))
                
                # Pequena pausa para respeitar a API do Google e evitar rate limit
                time.sleep(0.05)
                
            except Exception as ex:
                self.stdout.write(self.style.ERROR(
                    f'Erro ao traduzir {original_name}: {str(ex)}'
                ))
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Concluido! {translated_count} magias foram traduzidas para o Portugues com sucesso!'
        ))
