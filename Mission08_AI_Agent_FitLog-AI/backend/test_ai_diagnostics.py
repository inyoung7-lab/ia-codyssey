"""Offline Ollama validation and fallback tests; no external requests."""
import json
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend.ai_feedback import generate_feedback, validate_feedback, get_ai_settings
from backend.workout_analysis import analyze_workouts
from backend.workout_facts import build_facts, rules_feedback

class LocalAITests(unittest.TestCase):
    def setUp(self):
        self.row={'date':'2026-09-28','value':60,'memo':'private arbitrary memo'}
        self.analysis=analyze_workouts([self.row])
        self.facts=build_facts(self.analysis)
        self.safe=rules_feedback(self.facts)

    def mock_response(self, client, content):
        response=client.return_value.__enter__.return_value.post.return_value
        response.json.return_value={'model':'hermes3:8b','done':True,'done_reason':'stop','message':{'content':content}}
        return response

    def test_success_and_minimal_payload(self):
        with patch('backend.ai_feedback.get_ai_settings',return_value=('http://127.0.0.1:11434','hermes3:8b')), patch('backend.ai_feedback.httpx.Client') as client:
            self.mock_response(client,json.dumps(self.safe))
            result=generate_feedback(self.analysis)
            self.assertEqual(result,{'provider':'ollama','ai_feedback':self.safe})
            request=client.return_value.__enter__.return_value.post
            request.assert_called_once()
            self.assertEqual(request.call_args.args[0],'http://127.0.0.1:11434/api/chat')
            payload=request.call_args.kwargs['json']
            self.assertIn('format',payload)
            self.assertNotIn(self.row['memo'],str(payload))
            self.assertEqual(json.loads(payload['messages'][1]['content']),{'FACTS':self.facts})

    def test_failures_return_rules_without_raw_logs(self):
        for failure in ['connection','timeout','invalid_json','schema','unsafe','http']:
            with self.subTest(failure=failure), patch('backend.ai_feedback.get_ai_settings',return_value=('http://127.0.0.1:11434','hermes3:8b')), patch('backend.ai_feedback.httpx.Client') as client:
                response=self.mock_response(client,json.dumps(self.safe))
                post=client.return_value.__enter__.return_value.post
                if failure=='connection': post.side_effect=httpx.ConnectError('SECRET_SENTINEL')
                if failure=='timeout': post.side_effect=httpx.ReadTimeout('SECRET_SENTINEL')
                if failure=='invalid_json': response.json.side_effect=ValueError('SECRET_SENTINEL')
                if failure=='schema': self.mock_response(client,'{}')
                if failure=='unsafe': self.mock_response(client,json.dumps({**self.safe,'summary':'SECRET_SENTINEL'}))
                if failure=='http': response.raise_for_status.side_effect=RuntimeError('SECRET_SENTINEL')
                with self.assertLogs('backend.ai_feedback',level='WARNING') as logs:
                    result=generate_feedback(self.analysis)
                self.assertEqual(result,{'provider':'rules','ai_feedback':self.safe})
                self.assertNotIn('SECRET_SENTINEL',str(logs.output))
                post.assert_called_once()

    def test_rejects_new_numbers_foreign_text_and_swapped_facts(self):
        for text in ['999분 운동했습니다.','健康이 좋아졌습니다.','운동량을 늘리세요.','휴식이 부족합니다.','꾸준한 습관이 형성되었습니다.','운동일은 0일입니다.','운동한 날의 평균 운동시간은 0분입니다.','']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_feedback({**self.safe,'summary':text},self.facts)
        self.assertEqual(validate_feedback(self.safe,self.facts),self.safe)
        with self.assertRaises(ValueError): validate_feedback({**self.safe,'extra':'x'},self.facts)

    def test_configuration_only_reads_local_variables(self):
        reads=[]
        def getenv(name,default=None):
            reads.append(name)
            self.assertIn(name,{'OLLAMA_BASE_URL','OLLAMA_MODEL'})
            return default
        with patch('backend.ai_feedback.os.getenv',side_effect=getenv):
            self.assertEqual(get_ai_settings(),('http://127.0.0.1:11434','hermes3:8b'))
        with patch('backend.ai_feedback.os.getenv',side_effect=lambda name,default: 'https://example.com' if name=='OLLAMA_BASE_URL' else default):
            with self.assertRaises(ValueError): get_ai_settings()

    def test_endpoint_and_empty(self):
        with patch('backend.main._read_workouts',return_value=[self.row]), patch('backend.ai_feedback.httpx.Client') as client, patch('backend.ai_feedback.get_ai_settings',return_value=('http://127.0.0.1:11434','hermes3:8b')), TestClient(app) as api:
            client.return_value.__enter__.return_value.post.side_effect=httpx.ConnectError('offline')
            response=api.get('/workouts/ai-analysis')
            self.assertEqual(response.status_code,200)
            self.assertEqual(set(response.json()),{'provider','period','statistics','ai_feedback'})
            self.assertEqual(response.json()['provider'],'rules')
            self.assertEqual(api.get('/health').status_code,200)
        with patch('backend.main._read_workouts',return_value=[]), patch('backend.main.generate_feedback') as generate, TestClient(app) as api:
            self.assertEqual(api.get('/workouts/ai-analysis').status_code,404)
            generate.assert_not_called()

    def test_facts_gaps_zero_and_ties(self):
        rows=[{'date':'2026-09-27','value':10,'memo':'러닝'},{'date':'2026-09-28','value':10,'memo':'걷기'}]
        facts=build_facts(analyze_workouts(rows))
        self.assertTrue(any('러닝, 걷기' in s and '각각 1회' in s for s in facts['strength']))
        self.assertTrue(any('28일' in s for s in facts['improvement']))
        self.assertNotIn('%',facts['summary'][-1])
        self.assertEqual(generate_feedback(analyze_workouts([]))['provider'],'rules')

if __name__=='__main__': unittest.main()
