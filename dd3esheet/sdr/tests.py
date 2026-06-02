import json
import tempfile
import os
from django.test import TestCase
from django.core.management import call_command
from django.db import connections
from sdr.lookups import resolve_spell
from sdr.models import SDR_Feat, SDR_Spell

class SDRFeatTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cria a tabela 'feat' no banco de testes 'sdr' pois possui managed = False
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    multiple TEXT,
                    stack TEXT,
                    choice TEXT,
                    prerequisite TEXT,
                    benefit TEXT,
                    normal TEXT,
                    special TEXT,
                    full_text TEXT,
                    reference TEXT
                );
            """)

    def test_import_feats_command(self):
        # Cria um arquivo JSON temporario para testar
        temp_data = [
            {
                "name": "Ataque Especial Teste",
                "type": "General",
                "prerequisite": "Nenhum",
                "benefit": "Concede +2 de dano de teste.",
                "reference": "Livro de Teste (PT)"
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w+', delete=False, encoding='utf-8') as f:
            json.dump(temp_data, f)
            temp_file_path = f.name

        try:
            # Chama o comando passando o arquivo temporario
            call_command('import_feats', file=temp_file_path)
            
            # Verifica se foi criado com sucesso no banco sdr
            qs = SDR_Feat.objects.using('sdr').filter(name="Ataque Especial Teste")
            self.assertTrue(qs.exists())
            feat = qs.first()
            self.assertEqual(feat.benefit, "Concede +2 de dano de teste.")
            self.assertEqual(feat.reference, "Livro de Teste (PT)")
            
            # Testa a atualizacao do talento
            temp_data[0]["benefit"] = "Concede +4 de dano de teste atualizado."
            with open(temp_file_path, 'w', encoding='utf-8') as f_write:
                json.dump(temp_data, f_write)
                
            call_command('import_feats', file=temp_file_path)
            
            feat.refresh_from_db(using='sdr')
            self.assertEqual(feat.benefit, "Concede +4 de dano de teste atualizado.")
            
        finally:
            # Garante a limpeza do banco de testes e do arquivo
            SDR_Feat.objects.using('sdr').filter(name="Ataque Especial Teste").delete()
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class SDRSpellTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Cria a tabela 'spell' no banco de testes 'sdr' pois possui managed = False
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    school TEXT,
                    subschool TEXT,
                    descriptor TEXT,
                    spellcraft_dc TEXT,
                    level TEXT,
                    components TEXT,
                    casting_time TEXT,
                    range TEXT,
                    target TEXT,
                    area TEXT,
                    effect TEXT,
                    duration TEXT,
                    saving_throw TEXT,
                    spell_resistance TEXT,
                    short_description TEXT,
                    to_develop TEXT,
                    material_components TEXT,
                    arcane_material_components TEXT,
                    focus TEXT,
                    description TEXT,
                    xp_cost TEXT,
                    arcane_focus TEXT,
                    wizard_focus TEXT,
                    verbal_components TEXT,
                    sorcerer_focus TEXT,
                    bard_focus TEXT,
                    cleric_focus TEXT,
                    druid_focus TEXT,
                    full_text TEXT,
                    reference TEXT
                );
            """)

    def test_import_spells_command(self):
        # 1. Cadastra uma magia ficticia original em ingles na base de testes
        original_spell = SDR_Spell(
            name="Magic Missile",
            school="Evocation",
            level="Sor/Wiz 1",
            description="An original English description."
        )
        original_spell.save(using='sdr')

        # 2. Cria um arquivo JSON temporario contendo a traducao em portugues
        temp_data = [
            {
                "name": "Misseis Magicos",
                "altname": "Magic Missile",
                "school": "Evocation",
                "level": "Sor/Wiz 1",
                "description": "Uma descricao traduzida em portugues.",
                "reference": "Livro do Jogador (PT)"
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w+', delete=False, encoding='utf-8') as f:
            json.dump(temp_data, f)
            temp_file_path = f.name

        try:
            # 3. Executa o comando de importacao
            call_command('import_spells', file=temp_file_path)
            
            # 4. Verifica se a magia original em ingles foi traduzida in-place
            qs = SDR_Spell.objects.using('sdr').filter(altname="Magic Missile")
            self.assertTrue(qs.exists())
            self.assertEqual(qs.count(), 1) # Sem duplicatas!
            
            spell = qs.first()
            self.assertEqual(spell.name, "Misseis Magicos")
            self.assertEqual(spell.description, "Uma descricao traduzida em portugues.")
            self.assertEqual(spell.reference, "Livro do Jogador (PT)")
            
        finally:
            # Garante limpeza
            SDR_Spell.objects.using('sdr').filter(name="Misseis Magicos").delete()
            SDR_Spell.objects.using('sdr').filter(name="Magic Missile").delete()
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)


class ResolveSpellTests(TestCase):
    databases = {'sdr', 'default'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connections['sdr'].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    altname TEXT,
                    school TEXT, subschool TEXT, descriptor TEXT,
                    spellcraft_dc TEXT, level TEXT, components TEXT,
                    casting_time TEXT, range TEXT, target TEXT, area TEXT,
                    effect TEXT, duration TEXT, saving_throw TEXT,
                    spell_resistance TEXT, short_description TEXT,
                    to_develop TEXT, material_components TEXT,
                    arcane_material_components TEXT, focus TEXT,
                    description TEXT, xp_cost TEXT,
                    arcane_focus TEXT, wizard_focus TEXT,
                    verbal_components TEXT, sorcerer_focus TEXT,
                    bard_focus TEXT, cleric_focus TEXT, druid_focus TEXT,
                    full_text TEXT, reference TEXT
                );
            """)

    def setUp(self):
        SDR_Spell.objects.using('sdr').all().delete()
        SDR_Spell(name="Magic Missile", altname="Misseis Magicos",
                  school="Evocation", level="Sor/Wiz 1").save(using='sdr')

    def test_match_by_name_case_insensitive(self):
        self.assertEqual(resolve_spell("magic missile").name, "Magic Missile")
        self.assertEqual(resolve_spell("MAGIC MISSILE").name, "Magic Missile")

    def test_match_by_altname_when_name_misses(self):
        self.assertEqual(resolve_spell("Misseis Magicos").name, "Magic Missile")

    def test_returns_none_for_empty(self):
        self.assertIsNone(resolve_spell(""))
        self.assertIsNone(resolve_spell(None))
        self.assertIsNone(resolve_spell("   "))

    def test_returns_none_for_unknown(self):
        self.assertIsNone(resolve_spell("Bola de Fogo Tropical"))

    def test_ambiguity_returns_first_by_id(self):
        first = SDR_Spell.objects.using('sdr').get(name="Magic Missile")
        duplicate = SDR_Spell(name="Magic Missile", school="X")
        duplicate.save(using='sdr')
        result = resolve_spell("Magic Missile")
        self.assertEqual(result.id, first.id)
        self.assertEqual(result.school, "Evocation")
