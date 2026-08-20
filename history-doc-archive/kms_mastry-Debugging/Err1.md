## Troubleshooting Odoo Invalid Field Error

RPC_ERROR

Odoo Server Error

Occured on localhost:8069 on model ir.module.module on 2026-08-17 21:04:50 GMT

Traceback (most recent call last):
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 608, in _tag_root
    f(rec)
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 463, in _tag_record
    record = model._load_records([data], self.mode == 'update')
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 5196, in _load_records
    records = self._load_records_create([data['values'] for data in to_create])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 5103, in _load_records_create
    records = self.create(vals_list)
              ^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\decorators.py", line 369, in create
    return method(self, vals_list)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\addons\base\models\res_groups.py", line 299, in create
    groups = super().create(vals_list)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\decorators.py", line 369, in create
    return method(self, vals_list)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 4654, in create
    raise ValueError(f"Invalid field {field_name!r} in {self._name!r}")
ValueError: Invalid field 'category_id' in 'res.groups'

The above exception was the direct cause of the following exception:

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
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 621, in _tag_root
    raise ParseError('while parsing %s:%s, somewhere inside\n%s' % (
odoo.tools.convert.ParseError: while parsing file:/c:/users/aniru/documents/odoo19devenv/custom_addons/kms_mastery/security/kms_security.xml:10, somewhere inside
<record id="group_kms_learner" model="res.groups">
        <field name="name">Learner</field>
        <field name="category_id" ref="module_category_kms"/>
    </record>

The above server error caused the following client error:
RPC_ERROR: Odoo Server Error
    RPC_ERROR
        at makeErrorFromResponse (http://localhost:8069/web/assets/b8779ba/web.assets_web.min.js:3195:165)
        at XMLHttpRequest.<anonymous> (http://localhost:8069/web/assets/b8779ba/web.assets_web.min.js:3202:13)

---

Above is the error log recieved while trying to install custom_addons\kms_mastery, find the root cause

---
---

Viewed res_groups.py:1-100
Searched for "model="res.groups""
Viewed survey_security.xml:1-40
Viewed kms_security.xml:1-133
Searched for "class ResGroupsPrivilege"
Viewed res_groups_privilege.py:1-15
Searched for "model="res.groups.privilege""
Viewed project_security.xml:1-30
Viewed ir.model.access.csv:1-24

### Root Cause

In **Odoo 19**, the access rights and security group architecture was updated:
1. **The `category_id` field has been removed from `res.groups`**.
2. Odoo 19 introduced the intermediate model **`res.groups.privilege`**, which now holds the reference to `category_id` (`ir.module.category`).
3. Records on `res.groups` now associate with privileges using the field **`privilege_id`** (many2one to `res.groups.privilege`) rather than linking directly to `ir.module.category`.

In [kms_security.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/security/kms_security.xml#L10-L19), `group_kms_learner` and `group_kms_instructor` are defining `<field name="category_id" ref="..."/>`:

```xml
    <!-- Security Groups -->
    <record id="group_kms_learner" model="res.groups">
        <field name="name">Learner</field>
        <field name="category_id" ref="module_category_kms"/> <!-- ❌ Invalid field in Odoo 19 -->
    </record>

    <record id="group_kms_instructor" model="res.groups">
        <field name="name">Instructor</field>
        <field name="category_id" ref="module_category_kms"/> <!-- ❌ Invalid field in Odoo 19 -->
        <field name="implied_ids" eval="[(4, ref('group_kms_learner'))]"/>
    </record>
```

---

### How to Fix

To conform to Odoo 19 standards, define a `res.groups.privilege` record under your category and link your groups to it using `privilege_id`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Module Category -->
    <record id="module_category_kms" model="ir.module.category">
        <field name="name">KMS Mastery Learning</field>
        <field name="sequence">100</field>
    </record>

    <!-- Group Privilege -->
    <record id="res_groups_privilege_kms" model="res.groups.privilege">
        <field name="name">KMS Mastery</field>
        <field name="category_id" ref="module_category_kms"/>
        <field name="sequence">10</field>
    </record>

    <!-- Security Groups -->
    <record id="group_kms_learner" model="res.groups">
        <field name="name">Learner</field>
        <field name="privilege_id" ref="res_groups_privilege_kms"/>
        <field name="sequence">10</field>
    </record>

    <record id="group_kms_instructor" model="res.groups">
        <field name="name">Instructor</field>
        <field name="privilege_id" ref="res_groups_privilege_kms"/>
        <field name="sequence">20</field>
        <field name="implied_ids" eval="[(4, ref('group_kms_learner'))]"/>
    </record>
...
```

---

Viewed kms_security.xml:1-25
Searched for "category_id"
Searched for "group_kms_"
Edited kms_security.xml
Viewed kms_security.xml:1-35

The issue has been resolved in [kms_security.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/security/kms_security.xml).

### Changes Made
1. **Added `res.groups.privilege` Record**: Created `res_groups_privilege_kms` under category `module_category_kms`.
2. **Updated `res.groups` Records**: Replaced the deprecated `category_id` references on `group_kms_learner` and `group_kms_instructor` with `privilege_id` linking to `res_groups_privilege_kms`.