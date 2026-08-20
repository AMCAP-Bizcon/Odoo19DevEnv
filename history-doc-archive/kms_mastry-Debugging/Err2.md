## Debugging Odoo Module Installation

RPC_ERROR

Odoo Server Error

Occured on localhost:8069 on model ir.module.module on 2026-08-17 21:16:51 GMT

Traceback (most recent call last):
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\http.py", line 2329, in _serve_db
    return service_model.retrying(serve_func, env=self.env)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\service\model.py", line 188, in retrying
    result = func()
             ^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\http.py", line 2384, in _serve_ir_http
    response = self.dispatcher.dispatch(rule.endpoint, args)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\http.py", line 2599, in dispatch
    result = self.request.registry['ir.http']._dispatch(endpoint)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\addons\base\models\ir_http.py", line 353, in _dispatch
    result = endpoint(**request.params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\http.py", line 838, in route_wrapper
    result = endpoint(self, *args, **params_ok)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\users\aniru\documents\odoo19devenv\odoo\addons\web\controllers\dataset.py", line 38, in call_button
    action = call_kw(request.env[model], method, args, kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\service\model.py", line 97, in call_kw
    result = method(recs, *args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\addons\base\models\ir_module.py", line 72, in check_and_log
    return method(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\addons\base\models\ir_module.py", line 493, in button_immediate_install
    return self._button_immediate_function(self.env.registry[self._name].button_install)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\addons\base\models\ir_module.py", line 638, in _button_immediate_function
    registry = modules.registry.Registry.new(self.env.cr.dbname, update_module=True)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\func.py", line 88, in locked
    return func(inst, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\registry.py", line 189, in new
    load_modules(
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\modules\loading.py", line 464, in load_modules
    load_module_graph(
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\modules\loading.py", line 217, in load_module_graph
    load_data(env, idref, 'init', kind='data', package=package)
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\modules\loading.py", line 59, in load_data
    convert_file(env, package.name, filename, idref, mode, noupdate=kind == 'demo')
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 696, in convert_file
    convert_xml_import(env, module, fp, idref, mode, noupdate)
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 795, in convert_xml_import
    obj.parse(doc.getroot())
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 666, in parse
    self._tag_root(de)
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 619, in _tag_root
    raise ParseError(msg) from None  # Restart with "--log-handler odoo.tools.convert:DEBUG" for complete traceback
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
odoo.tools.convert.ParseError: while parsing file:/c:/users/aniru/documents/odoo19devenv/custom_addons/kms_mastery/views/kms_course_views.xml:5
Invalid view kms.course.view.search definition in kms_mastery/views/kms_course_views.xml

View error context:
'-no context-'


The above server error caused the following client error:
RPC_ERROR: Odoo Server Error
    RPC_ERROR
        at makeErrorFromResponse (http://localhost:8069/web/assets/b8779ba/web.assets_web.min.js:3195:165)
        at XMLHttpRequest.<anonymous> (http://localhost:8069/web/assets/b8779ba/web.assets_web.min.js:3202:13)

---

Above is the error log recieved while trying to install custom_addons\kms_mastery, find the root cause

---
---

Viewed kms_course_views.xml:1-148
Listed directory models
Viewed kms_course.py:1-84
Viewed __manifest__.py:1-48
Searched for "%("
Searched for "domain="
Searched for "domain="
Searched for "groups_id"
Searched for "[('groups_id"
Searched for "lambda self:"
Viewed kms_node_views.xml:1-121
Viewed kms_security.xml:1-142
Viewed kms_quiz_views.xml:1-60
Viewed kms_quiz_views.xml:61-120
Viewed kms_flashcard_views.xml:1-60

### Root Cause

The error occurs because of an **invalid domain definition on the Python model field `instructor_id`** in [custom_addons/kms_mastery/models/kms_course.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_course.py#L19-L24):

```python
instructor_id = fields.Many2one(
    'res.users',
    string='Primary Instructor',
    domain="[('groups_id', 'in', %(kms_mastery.group_kms_instructor)d)]",  # <-- ROOT CAUSE
    tracking=True,
)
```

#### Why this causes `ParseError: Invalid view kms.course.view.search definition`:
1. The syntax `%(module.xml_id)d` is **only valid inside XML files**, where Odoo's XML parser replaces it with the database ID.
2. In Python model definitions, `"['groups_id', 'in', %(...)]"` is stored as a raw string.
3. When Odoo parses and validates [kms_course_views.xml:5](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/views/kms_course_views.xml#L5-L19) (`kms_course_view_search`), it encounters `<field name="instructor_id"/>` and attempts to evaluate the field's domain using Python's AST parser / `safe_eval`.
4. Because `%(kms_mastery.group_kms_instructor)d` is invalid Python syntax, parsing fails and Odoo marks the search view as invalid.

---

### How to Fix

#### 1. Fix `instructor_id` in [kms_course.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_course.py#L19-L24)
Use a `lambda` callable to evaluate the XML ID dynamically in Python:

```python
instructor_id = fields.Many2one(
    'res.users',
    string='Primary Instructor',
    domain=lambda self: [('groups_id', 'in', self.env.ref('kms_mastery.group_kms_instructor').id)],
    tracking=True,
)
```

---

### ⚠️ Secondary Issue to Fix: XML File Loading Order in `__manifest__.py`

Once the view validation error is resolved, you will hit an **External ID not found** error due to the load order in [__manifest__.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/__manifest__.py#L27-L35):

* `kms_course_views.xml` references `%(kms_mastery.kms_node_action)d` (defined in `kms_node_views.xml`).
* `kms_node_views.xml` references `%(kms_mastery.kms_quiz_question_action)d` and `%(kms_mastery.kms_flashcard_action)d` (defined in `kms_quiz_views.xml` and `kms_flashcard_views.xml`).

**Recommended loading order in `__manifest__.py`:**
```python
    'data': [
        # Security (must load first)
        'security/kms_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        # Views (ordered by action dependencies)
        'views/kms_quiz_views.xml',
        'views/kms_flashcard_views.xml',
        'views/kms_node_views.xml',
        'views/kms_milestone_views.xml',
        'views/kms_course_views.xml',
        'views/kms_learner_views.xml',
        'views/kms_menus.xml',
    ],
```

---

Viewed kms_milestone.py:1-39
Viewed kms_milestone_views.xml:1-187
Viewed kms_menus.xml:1-119
Viewed kms_learner_views.xml:1-60
Edited kms_course.py
Edited __manifest__.py

Both issues have been fixed:

1. **Fixed `instructor_id` domain in [kms_course.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_course.py#L19-L24):**
   Replaced the static XML ID format string `"%(kms_mastery.group_kms_instructor)d"` with a dynamic `lambda` expression:
   ```python
   instructor_id = fields.Many2one(
       'res.users',
       string='Primary Instructor',
       domain=lambda self: [('groups_id', 'in', self.env.ref('kms_mastery.group_kms_instructor').id)],
       tracking=True,
   )
   ```

2. **Fixed view file loading order in [__manifest__.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/__manifest__.py#L27-L36):**
   Reordered the view files in `'data'` so actions referenced across views (e.g. `kms_quiz_question_action`, `kms_flashcard_action`, and `kms_node_action`) are defined before the views that reference them.