import unittest
from financial_chronology_audit import audit_cash_chronology_rows

class AuditTests(unittest.TestCase):
    def test_overlap_and_deduplication(self):
        a={'transaction_cycle':{'available':True,'initial_at':'2026-10-01T10:00:00','final_at':'2026-10-08T10:00:00'}}
        b={'transaction_cycle':{'available':True,'initial_at':'2026-10-07T10:00:00','final_at':'2026-10-09T10:00:00'}}
        result=audit_cash_chronology_rows([{'terminal':'32551','planned':[a,a,b],'extra':[]}])
        self.assertEqual(result['atms_with_issues'],1)
        self.assertEqual(sum(i['type']=='JANELAS_SOBREPOSTAS' for i in result['issues']),1)
    def test_valid_sequence(self):
        a={'transaction_cycle':{'available':True,'initial_at':'2026-09-24T10:00:00','final_at':'2026-10-01T10:00:00'}}
        b={'transaction_cycle':{'available':True,'initial_at':'2026-10-01T10:00:00','final_at':'2026-10-08T10:00:00'}}
        result=audit_cash_chronology_rows([{'terminal':'32551','planned':[a,b]}])
        self.assertEqual(result['atms_with_issues'],0)
    def test_missing_reference(self):
        a={'date':'2026-10-01','transaction_cycle':{'available':False,'chronology_audit':{'status':'SEM_REFERENCIA_R0050'}}}
        result=audit_cash_chronology_rows([{'terminal':'1','extra':[a]}])
        self.assertEqual(result['atms_with_issues'],1)
if __name__=='__main__':unittest.main()
