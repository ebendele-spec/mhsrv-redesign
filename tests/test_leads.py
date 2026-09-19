"""Regression checks for restored intake coverage, routing and accessible forms."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import lead_templates as leads


class Document(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.elements = []
        self.forms = {}
        self.form = None
        self.feed(markup)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.elements.append((tag, attrs))
        if tag == 'form':
            self.form = attrs['id']
            self.forms[self.form] = []
        elif self.form and tag in ('input', 'select', 'textarea'):
            self.forms[self.form].append(attrs)

    def handle_endtag(self, tag):
        if tag == 'form':
            self.form = None


class LeadTemplatesTest(unittest.TestCase):
    config = {'leadEmail': 'elisha@mhsrv.com'}

    def test_every_original_meaningful_rv_and_auto_field_is_present(self):
        document = Document(leads.trade_page(self.config))
        for kind, count in [('rv', 115), ('auto', 63)]:
            original = {field['name'] for group in leads.SCHEMA[kind] for field in group['fields']}
            self.assertEqual(len(original), count)
            rendered = {field['name'] for field in document.forms['trade-' + kind]}
            self.assertTrue((original - leads.OLD_MARKETING) <= rendered)
            self.assertFalse(rendered & leads.OLD_MARKETING)

    def test_separate_unchecked_optional_consents_and_required_routing(self):
        for renderer in [leads.trade_page, leads.sell_page, leads.finance_page]:
            for fields in Document(renderer(self.config)).forms.values():
                by_name = {field['name']: field for field in fields}
                for consent in ['marketing_email_consent', 'marketing_sms_consent']:
                    self.assertEqual(by_name[consent]['type'], 'checkbox')
                    self.assertNotIn('checked', by_name[consent])
                    self.assertNotIn('required', by_name[consent])
                for name in ['name', 'location', 'date', 'sales_representative']:
                    self.assertIn('required', by_name[name])
                self.assertNotIn('required', by_name['email'])
                self.assertNotIn('required', by_name['confirm_email'])
                self.assertIn('data-email-confirmation', by_name['confirm_email'])

    def test_unique_ids_and_resolvable_labels_and_tab_controls(self):
        for renderer in [leads.trade_page, leads.sell_page, leads.finance_page]:
            document = Document(renderer(self.config) + leads.contact_dialog('', self.config))
            ids = [attrs['id'] for _, attrs in document.elements if 'id' in attrs]
            self.assertEqual(len(ids), len(set(ids)))
            for _, attrs in document.elements:
                for attribute in ['for', 'aria-controls', 'aria-labelledby']:
                    if attribute in attrs:
                        self.assertTrue(all(value in ids for value in attrs[attribute].split()))

    def test_no_sensitive_credit_fields_and_explicit_finance_inquiry(self):
        markup = leads.finance_page(self.config)
        document = Document(markup)
        fields = {field['name'] for field in document.forms['finance-intake']}
        self.assertTrue({'purchase_budget', 'monthly_budget', 'unit_of_interest', 'down_payment_amount', 'down_payment_percent', 'timeframe', 'illustrative_apr', 'term_months'} <= fields)
        self.assertFalse(fields & {'ssn', 'social_security_number', 'bank_account', 'routing_number', 'income', 'date_of_birth'})
        self.assertIn('not a credit application', markup)
        self.assertIn('does not check your credit', markup)

    def test_contact_dialog_preserves_shared_hooks_and_phone_only_path(self):
        document = Document(leads.contact_dialog('../', self.config))
        ids = {attrs['id'] for _, attrs in document.elements if 'id' in attrs}
        self.assertTrue({'leadDialog', 'leadForm', 'leadTitle', 'leadContext', 'leadName', 'leadEmail', 'leadPhone', 'leadMessage'} <= ids)
        fields = {field['name']: field for field in document.forms['leadForm']}
        self.assertIn('required', fields['name'])
        self.assertNotIn('required', fields['email'])
        self.assertNotIn('required', fields['phone'])
        links = [attrs for tag, attrs in document.elements if tag == 'a']
        self.assertTrue(any(attrs.get('href') == 'mailto:elisha@mhsrv.com' for attrs in links))
        self.assertTrue(any(attrs.get('href') == '../privacy.html' for attrs in links))
        self.assertTrue(any('data-lead-sms' in attrs for attrs in links))


if __name__ == '__main__':
    unittest.main()
