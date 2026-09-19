"""Accessible inquiry and appraisal-intake bodies; wrapped by the shared site document."""
import html
import json
from pathlib import Path

E = lambda value: html.escape(str(value if value is not None else ''), quote=True)
SCHEMA = json.loads((Path(__file__).with_name('intake-fields.json')).read_text())['forms']
CONTACT_NAMES = {'location', 'date', 'name', 'preferred_phone', 'email', 'confirm_email', 'sales_representative'}
OLD_MARKETING = {'news_letter', 'be_the_first_to_see_exclusive_weekly_specials_on'}
LOCATIONS = [('MHS Texas', 'Alvarado, Texas'), ('MHS Alabama', 'Montgomery, Alabama'), ('MHS California', 'Palm Desert, California')]
REPRESENTATIVES = [('Please assign a specialist', 'Please assign a specialist'), ('Already working with a specialist', 'Already working with a specialist'), ('Not sure', 'Not sure')]


def spec(name, label, kind='text', required=False, options=None, **extra):
    item = dict(name=name, label=label, type=kind, required=required, **extra)
    if options is not None:
        item['options'] = [{'value': v, 'label': label} for v, label in options]
    return item


def render_field(field, prefix):
    f = dict(field)
    name, kind = f['name'], f['type']
    label = f['label']
    required = f.get('required', False) and name not in {'email', 'preferred_phone', 'phone', 'confirm_email'}
    if name == 'location':
        f['options'] = [{'value': '', 'label': 'Choose a location'}] + [dict(value=v, label=l) for v, l in LOCATIONS]
    if name == 'sales_representative':
        f['options'] = [{'value': '', 'label': 'Choose an option'}] + [dict(value=v, label=l) for v, l in REPRESENTATIVES]
    labels = {'preferred_phone': 'Phone number', 'confirm_email': 'Confirm email (if provided)', 'miles': 'Mileage (enter 0 for a towable)', 'date': 'Request date'}
    label = labels.get(name, label)
    fid = prefix + '-' + name
    req = ' required' if required else ''
    mark = ' <span class="intake-required" aria-hidden="true">*</span>' if required else ''
    full = ' intake-wide' if kind in ('textarea', 'checkbox') or len(label) > 65 else ''
    attributes = f' name="{E(name)}" data-field-label="{E(label)}"{req}'
    autocomplete = {'name': 'name', 'email': 'email', 'preferred_phone': 'tel', 'phone': 'tel'}.get(name, 'off')
    if kind in ('radio', 'checkbox'):
        options = list(f.get('options', []))
        if kind == 'radio' and not any('not sure' in x['value'].lower() for x in options):
            options.append({'value': 'Not sure / not applicable', 'label': 'Not sure / N/A'})
        controls = []
        for i, option in enumerate(options):
            value = option['value']
            ol = {'4': '4 · Excellent', '3': '3 · Good', '2': '2 · Fair', '1': '1 · Poor'}.get(value, option['label'])
            controls.append(f'<label class="intake-choice" for="{E(fid)}-{i}"><input id="{E(fid)}-{i}" type="{kind}"{attributes} value="{E(value)}"><span>{E(ol)}</span></label>')
        return f'<fieldset class="intake-field intake-options{full}"><legend>{E(label)}{mark}</legend><div class="intake-choice-list">{"".join(controls)}</div></fieldset>'
    if kind == 'select':
        options = list(f.get('options', []))
        if name not in {'location', 'sales_representative', 'preferred_contact'} and not any('not sure' in x['value'].lower() for x in options):
            options.append({'value': 'Not sure / not applicable', 'label': 'Not sure / not applicable'})
        control = f'<select id="{E(fid)}"{attributes}>' + ''.join(f'<option value="{E(o["value"])}">{E(o["label"])}</option>' for o in options) + '</select>'
    elif kind == 'textarea':
        control = f'<textarea id="{E(fid)}"{attributes} rows="4" maxlength="5000" placeholder="{E(f.get("placeholder", "Add the details you would like us to consider."))}"></textarea>'
    else:
        limit = '30' if kind == 'tel' else '180' if kind == 'email' else '300'
        extra = ' data-request-date' if kind == 'date' else ''
        extra += ' data-email-confirmation' if name == 'confirm_email' else ''
        extra += ' inputmode="numeric"' if name in {'year', 'miles', 'generator_hours', 'approximate_miles_on_tires'} else ''
        placeholder = f.get('placeholder', 'Include area or country code' if kind == 'tel' else 'None, if there is no damage' if name.startswith('describe_any_') else '')
        control = f'<input id="{E(fid)}" type="{E(kind)}"{attributes}{extra} autocomplete="{autocomplete}" maxlength="{limit}" placeholder="{E(placeholder)}">'
    return f'<div class="intake-field{full}"><label for="{E(fid)}">{E(label)}{mark}</label>{control}</div>'


def contact_fields():
    return [spec('name', 'Your name', required=True), spec('phone', 'Phone number', 'tel'), spec('email', 'Email address', 'email'), spec('confirm_email', 'Confirm email (if provided)', 'email'), spec('preferred_contact', 'How should we reply?', 'select', options=[('', 'Either email or phone'), ('email', 'Email me'), ('call', 'Call me'), ('text', 'Text me')]), spec('location', 'Preferred location', 'select', True), spec('date', 'Request date', 'date', True), spec('sales_representative', 'Sales representative', 'select', True), spec('representative_name', 'Specialist’s name (if known)')]


def consents(prefix):
    return f'''<fieldset class="intake-consents"><legend>Stay in the loop <span>(optional)</span></legend><label for="{prefix}-marketing-email"><input type="checkbox" id="{prefix}-marketing-email" name="marketing_email_consent" value="Yes"><span>Email me MHSRV offers and news.</span></label><label for="{prefix}-marketing-sms"><input type="checkbox" id="{prefix}-marketing-sms" name="marketing_sms_consent" value="Yes"><span>Text me MHSRV offers and news. Message and data rates may apply.</span></label><p>These choices are optional and are not required to purchase or receive a reply to this inquiry.</p></fieldset>'''


def accordion_form(form_id, groups, subject, intent, config, vehicle=''):
    sections = []
    descriptions = ['Start with how to reach you. An email address or phone number is enough.', 'Tell us about your vehicle. Share what you know; uncertain answers are welcome.']
    for i, group in enumerate(groups):
        hint = group.get('hint', descriptions[i] if i < len(descriptions) else 'Complete the details you know. Choose “Not sure / N/A” where it fits.')
        fields = ''.join(render_field(f, form_id) for f in group['fields'])
        sections.append(f'''<details class="intake-step" data-intake-step{' open' if i == 0 else ''}><summary><span class="intake-step-number">{i+1:02}</span><span class="intake-step-title">{E(group['title'])}<small data-step-count>Ready when you are</small></span><span class="intake-step-chevron" aria-hidden="true">+</span></summary><div class="intake-step-body"><p class="intake-step-hint">{E(hint)}</p><div class="intake-fields">{fields}</div><div class="intake-step-actions"><button class="button outline small" type="button" data-intake-next>Continue to {E(groups[i+1]['title'] if i+1 < len(groups) else 'review')} <span aria-hidden="true">→</span></button></div></div></details>''')
    sections.append(f'''<details class="intake-step intake-review" data-intake-step><summary><span class="intake-step-number">{len(groups)+1:02}</span><span class="intake-step-title">Review &amp; send<small>Your information goes to an MHSRV specialist.</small></span><span class="intake-step-chevron" aria-hidden="true">+</span></summary><div class="intake-step-body"><div class="intake-review-summary" data-intake-review-summary>Your contact and vehicle details will appear here as you complete the form.</div>{consents(form_id)}<p class="form-note">By sending, you ask MHSRV to contact you about this request. This is an inquiry, not an appraisal, purchase agreement or credit application. Do not include Social Security numbers or financial account details. <a href="privacy.html">Privacy policy</a>.</p><button class="button yellow" type="submit">Send my inquiry <span aria-hidden="true">→</span></button><p class="form-message" role="status" tabindex="-1" hidden></p></div></details>''')
    return f'''<form id="{form_id}" class="intake-form" data-intake-form data-subject="{E(subject)}" method="post" action="#intake" novalidate><input type="hidden" name="intent" value="{E(intent)}"><input type="hidden" name="intake_type" value="{E(vehicle)}"><input type="hidden" name="stock"><div class="honeypot" aria-hidden="true"><label>Leave empty<input name="website" tabindex="-1" autocomplete="off"></label></div>{''.join(sections)}</form>'''


def page_open(eyebrow, heading, description):
    return f'<main id="main" class="container intake-page"><div class="page-heading"><p class="eyebrow">{E(eyebrow)}</p><h1>{E(heading)}</h1><p>{E(description)}</p></div><div class="intake-layout"><div id="intake">'


def page_close(config):
    email = E(config.get('leadEmail', 'elisha@mhsrv.com'))
    return f'''</div><aside class="intake-help"><span class="intake-help-icon" aria-hidden="true">↗</span><h2>A person on your side.</h2><p>Share the details once. An MHSRV specialist will help with the next step and confirm any missing information.</p><a href="tel:8003356054">Call 800-335-6054</a><a href="sms:8177907771" data-lead-sms>Text a specialist</a><a href="mailto:{email}">Email us</a><hr><p><b>Take it one section at a time.</b><br>Expand any section to review or change an answer. Required fields are marked with an asterisk. Your entries are kept only on this page until you send.</p><p class="form-note">Sending the form does not determine a trade value, approve financing or commit you to a purchase.</p></aside></div><noscript><p>Please enable JavaScript to send this form, or call 800-335-6054 or <a href="mailto:{email}">email MHSRV</a>.</p></noscript></main>'''


def trade_groups(kind):
    original = SCHEMA[kind]
    contact = [dict(f) for f in original[0]['fields'] if f['name'] in CONTACT_NAMES]
    contact += [spec('preferred_contact', 'How should we reply?', 'select', options=[('', 'Either email or phone'), ('email', 'Email me'), ('call', 'Call me'), ('text', 'Text me')]), spec('representative_name', 'Specialist’s name (if known)')]
    groups = [dict(title='You & your specialist', fields=contact), dict(title='Your RV' if kind == 'rv' else 'Your vehicle', fields=[f for f in original[0]['fields'] if f['name'] not in CONTACT_NAMES])]
    titles = {'rv': ['Powertrain & financing plans', 'Systems & equipment', 'Interior & exterior condition', 'History, tires & ownership', 'Features & final details'], 'auto': ['Equipment & options', 'Interior & exterior condition', 'History & financing plans']}
    for i, group in enumerate(original[1:]):
        groups.append(dict(title=titles[kind][i], fields=[f for f in group['fields'] if f['name'] not in OLD_MARKETING]))
    return groups


def trade_page(config):
    content = page_open('Make the next move', 'Let’s talk about your trade.', 'Bring the details. We’ll bring the RV expertise. Choose an RV or vehicle form and work through a few manageable sections.')
    content += '<div class="intake-tabs" role="tablist" aria-label="Trade-in type"><button type="button" role="tab" id="trade-tab-rv" aria-controls="trade-panel-rv" aria-selected="true" tabindex="0" data-intake-tab="rv">RV trade-in</button><button type="button" role="tab" id="trade-tab-auto" aria-controls="trade-panel-auto" aria-selected="false" tabindex="-1" data-intake-tab="auto">Car or truck trade-in</button></div><p class="intake-intro">Start with your contact and vehicle information. The equipment and condition sections help us prepare a useful conversation; the final value requires a specialist’s review.</p>'
    for kind in ('rv', 'auto'):
        content += f'<section id="trade-panel-{kind}" role="tabpanel" aria-labelledby="trade-tab-{kind}" data-intake-panel="{kind}"{ " hidden" if kind == "auto" else ""}>' + accordion_form('trade-' + kind, trade_groups(kind), 'MHSRV RV Trade-In Inquiry' if kind == 'rv' else 'MHSRV Auto Trade-In Inquiry', 'Trade-in inquiry', config, 'RV' if kind == 'rv' else 'Auto') + '</section>'
    return content + page_close(config)


def sell_page(config):
    groups = [dict(title='You & your specialist', fields=contact_fields()), dict(title='Your RV & your plans', fields=[spec('selling_goal', 'What would you like to explore?', 'select', True, [('', 'Choose an option'), ('Sell for cash', 'Sell my RV'), ('Trade toward another RV', 'Trade toward another RV'), ('Consignment', 'Explore consignment'), ('Discuss my options', 'Help me compare my options')]), spec('year', 'Model year', required=True), spec('make', 'Make / brand', required=True), spec('model', 'Model', required=True), spec('floorplan', 'Floorplan / model number'), spec('rv_type', 'RV type', 'select', options=[('', 'Choose a type'), ('Motorhome', 'Motorhome'), ('Camper van', 'Camper van'), ('Fifth wheel', 'Fifth wheel'), ('Travel trailer', 'Travel trailer'), ('Toy hauler', 'Toy hauler')]), spec('miles', 'Mileage (enter 0 for a towable)', required=True), spec('length', 'Length'), spec('vin', 'VIN (optional)'), spec('condition', 'Overall condition', 'select', options=[('', 'Choose an option'), ('Excellent', 'Excellent'), ('Good', 'Good'), ('Fair', 'Fair'), ('Needs attention', 'Needs attention')]), spec('asking_price', 'Your target selling price (optional)'), spec('timeframe', 'When would you like to make a move?', 'select', options=[('', 'Choose an option'), ('Soon', 'As soon as practical'), ('Within 30 days', 'Within 30 days'), ('Within 3 months', 'Within 3 months'), ('Exploring', 'Just exploring')])]), dict(title='History & anything else', fields=[spec('ownership', 'How long have you owned it?'), spec('lien', 'Is there an outstanding loan?', 'select', options=[('', 'Choose an option'), ('Yes', 'Yes'), ('No', 'No')]), spec('approximate_balance', 'Approximate remaining balance (optional)'), spec('service_history', 'Service history, upgrades and known issues', 'textarea'), spec('unit_of_interest', 'RV or stock number you’re interested in'), spec('message', 'Anything else you would like us to know?', 'textarea')])]
    return page_open('Sell · trade · consign', 'Your RV. Your next chapter.', 'Explore a sale, a trade or consignment with MHSRV. Tell us about your RV and what you have in mind; a specialist will discuss the available options.') + '<p class="intake-intro">Have detailed equipment and condition information ready? <a href="trade-in.html">Use the full RV or vehicle trade-in form</a>.</p>' + accordion_form('sell-intake', groups, 'MHSRV Sell / Trade / Consign Inquiry', 'Sell, trade or consign an RV', config, 'RV') + page_close(config)


def finance_page(config):
    groups = [dict(title='You & your specialist', fields=contact_fields()), dict(title='Build a comfortable starting point', hint='These are shopping preferences. Do not send income documents, account numbers or your Social Security number.', fields=[spec('purchase_budget', 'Target purchase budget'), spec('monthly_budget', 'Comfortable monthly payment'), spec('unit_of_interest', 'RV or stock number you’re interested in'), spec('down_payment_amount', 'Planned down payment ($)'), spec('illustrative_apr', 'Illustrative APR from your estimate (%)'), spec('term_months', 'Illustrative loan term (months)'), spec('down_payment_percent', 'Or planned down payment (%)', 'select', options=[('', 'Choose an option'), ('10%', '10%'), ('20%', '20%'), ('More than 20%', 'More than 20%'), ('Not sure yet', 'Not sure yet')]), spec('timeframe', 'When are you hoping to buy?', 'select', options=[('', 'Choose an option'), ('Now', 'Ready to talk now'), ('Within 30 days', 'Within 30 days'), ('Within 3 months', 'Within 3 months'), ('Later / exploring', 'Later / just exploring')]), spec('has_trade', 'Will you have a trade-in?', 'select', options=[('', 'Choose an option'), ('Yes', 'Yes'), ('No', 'No')]), spec('trade_details', 'Trade-in year, make and model (if applicable)'), spec('message', 'Questions for our finance team', 'textarea')])]
    return page_open('Plan the possibilities', 'Let’s explore your financing options.', 'Tell us your budget, the RV you’re considering and your timing. An MHSRV specialist can explain the next steps with you.') + '<div class="intake-notice"><strong>A conversation first.</strong> This inquiry is not a credit application, does not check your credit and does not prequalify or approve you for a loan. Any financing offer requires a separate lender application and approval.</div>' + accordion_form('finance-intake', groups, 'MHSRV Financing Inquiry', 'Discuss RV financing', config) + page_close(config)


def contact_dialog(prefix='', config=None):
    email = E((config or {}).get('leadEmail', 'elisha@mhsrv.com'))
    return f'''<dialog id="leadDialog" aria-labelledby="leadTitle"><div class="dialog-head"><div><div class="eyebrow">Your next step, made easy</div><h2 id="leadTitle">Talk to a specialist</h2></div><button class="icon-button" data-close aria-label="Close contact form">×</button></div><div class="dialog-body"><p id="leadContext">Tell us how to reach you. An MHSRV specialist can help with pricing, availability and the details that matter to you.</p><form class="lead-form" id="leadForm" method="post" action="#contact"><input type="hidden" name="intent" value="Talk to a specialist"><input type="hidden" name="stock"><div class="form-grid"><div class="field full"><label for="leadName">Your name</label><input id="leadName" name="name" autocomplete="name" required maxlength="120" placeholder="First and last name"></div><p class="intake-contact-hint full">An email address or phone number is enough. Choose whichever works for you.</p><div class="field full"><label for="leadEmail">Email address</label><input id="leadEmail" name="email" type="email" autocomplete="email" maxlength="180" placeholder="you@example.com"></div><div class="field full"><label for="leadPhone">Phone number</label><input id="leadPhone" name="phone" type="tel" autocomplete="tel" maxlength="30" placeholder="Include area or country code"></div><div class="field full"><label for="leadPreferredContact">How should we reply?</label><select id="leadPreferredContact" name="preferred_contact"><option value="">Either email or phone</option value="email">Email me</option><option value="call">Call me</option><option value="text">Text me</option></select></div><div class="field full"><label for="leadMessage">What would you like to know?</label><textarea id="leadMessage" name="message" maxlength="3000" placeholder="Ask a question, request a walk-through, or tell us about your trade."></textarea></div></div><div class="honeypot" aria-hidden="true"><label>Leave empty<input name="website" tabindex="-1" autocomplete="off"></label></div>{consents('contact')}<p class="form-note">By submitting, you ask MHSRV to contact you about this request. Your information is not posted publicly. <a href="{E(prefix)}privacy.html" data-privacy-link>Privacy policy</a>.</p><button class="button yellow" type="submit">Send my request →</button><div class="form-message" role="status" hidden></div></form><div class="contact-alternatives"><a href="tel:8003356054">Call us</a><a href="sms:8177907771" data-lead-sms>Text us</a><a href="mailto:{email}">Email us</a></div></div></dialog>'''
