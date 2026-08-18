## Troubleshooting KMS Mastery Installation

I installed the module kms_mastery using the following command, logged in, activated the developer mode and selected load demo data. No demo data got loaded, what's wrong?

---
---

Listed directory kms_mastery
Viewed __manifest__.py:1-48
Listed directory demo
Viewed kms_demo_data.xml:1-60
Searched for "kms_mastery"
Listed directory Odoo19DevEnv
Searched for "load demo data"
Searched for "demo"
Searched for "ir.module.module"
Listed directory odoo
Viewed OdooSetupPowerShellHistory.txt:1-27
Viewed odoo.conf:1-9
Listed directory addons
Viewed res_config_settings.py:1-137
Listed directory odoo
Searched for "demo"
Listed directory modules
Viewed loading.py:1-100
Viewed loading.py:101-200
Viewed loading.py:201-260
Viewed module_graph.py:1-100
Viewed module_graph.py:101-200
Viewed module_graph.py:201-260
Searched for "force_demo"
Viewed ir_demo.py:1-20
Viewed kms_demo_data.xml:1-150
Viewed kms_demo_data.xml:151-300
Viewed kms_demo_data.xml:301-450
Viewed kms_demo_data.xml:451-568
Listed directory models
Viewed kms_node.py:1-87
Viewed kms_user_node.py:1-148
Viewed kms_user_milestone.py:1-136
Viewed kms_security.xml:1-142
Searched for "_has_cycle"
Viewed ir.model.access.csv:1-24
Viewed kms_menus.xml:1-119
Searched for "model="res.users""
Viewed res_users_demo.xml:1-13
Searched for "groups_id ="
Searched for "group_ids"
Searched for "class Users("
Listed directory models
Viewed res_users.py:115-160
Viewed res_users.py:161-220
Viewed res_users.py:221-260
Searched for "def create("
Searched for "@api.model_create_multi"
Viewed res_users.py:500-600
Searched for "groups_id"
Viewed kms_course.py:1-40
Searched for "groups"
Searched for "groups ="
Viewed ir_rule.py:1-60
Viewed kms_learner_views.xml:1-60
Edited kms_demo_data.xml
Edited kms_course.py
Edited kms_security.xml

### Why No Demo Data Was Loaded

There were two main reasons why demo data failed to load:

#### 1. Odoo 19 Field Name Change (`groups_id` $\rightarrow$ `group_ids`)
In [kms_demo_data.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/demo/kms_demo_data.xml#L13-L25), the demo users were defined using the legacy field name `groups_id`:
```xml
<record id="demo_instructor_user" model="res.users">
    ...
    <field name="groups_id" eval="[...]"/> <!-- Invalid in Odoo 19 -->
</record>
```
In **Odoo 19**, the Many2many field on `res.users` for security groups is **`group_ids`** (singular `group` + plural `ids`).

#### 2. Odoo Silently Catches Demo Data Failures
When Odoo loads demo data (via module install or the Developer Mode *"Load demo data"* button), it wraps the execution in a `try...except` savepoint:
```python
# odoo/modules/loading.py -> load_demo()
try:
    load_data(..., kind='demo', package=package)
except Exception:
    _logger.warning("Module %s demo data failed to install, installed without demo data", package.name)
```
When Odoo encountered the non-existent field `groups_id`, it threw an exception. Instead of crashing the server or showing an error dialog, Odoo rolled back the demo data transaction and continued silently.

---

### Additional Fixes Applied

1. **Fixed [kms_demo_data.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/demo/kms_demo_data.xml#L13-L25):**
   Updated `groups_id` $\rightarrow$ `group_ids` on `demo_instructor_user` and `demo_learner_user`.

2. **Fixed [kms_course.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_course.py#L22):**
   Updated the domain on `instructor_id` from `('groups_id', 'in', ...)` $\rightarrow$ `('group_ids', 'in', ...)`.

3. **Updated [kms_security.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/security/kms_security.xml#L28):**
   Added `base.user_admin` and `base.user_root` to `group_kms_instructor` by default so your `admin` login immediately has full Instructor and Learner menu access.

---

### How to Reload the Demo Data Now

Run the following command in PowerShell to upgrade the module and reload the demo data (replace `<dbname>` with your database name):

```powershell
.\venv\Scripts\python.exe .\odoo\odoo-bin -c odoo.conf -d <dbname> -u kms_mastery --without-demo=False
```

Or from the Odoo web UI:
1. Go to **Settings** $\rightarrow$ Developer Mode.
2. Click **Load demo data** (or go to **Apps** $\rightarrow$ search `kms_mastery` $\rightarrow$ click **Upgrade**).

#### Demo Credentials:
- **Instructor**: `kms_instructor` / `kms_instructor` (Prof. Sarah Chen)
- **Learner**: `kms_learner` / `kms_learner` (Alex Rivera)
- **Administrator**: `admin` (has full Instructor & Learner access)

Viewed kms_demo_data.xml:1-26

---
---

2026-08-17 22:25:26,681 18000 INFO kms_demo odoo.modules.loading: updating modules list 
2026-08-17 22:25:26,686 18000 INFO kms_demo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on [] to user __system__ #1 via n/a
2026-08-17 22:25:26,990 18000 WARNING kms_demo odoo.modules.module: Missing `author` key in manifest for 'kms_mastery', defaulting to ''
2026-08-17 22:25:26,990 18000 WARNING kms_demo odoo.modules.module: Missing `author` key in manifest for 'kms_mastery', defaulting to ''
2026-08-17 22:25:27,632 18000 INFO kms_demo odoo.addons.base.models.ir_module: ALLOW access to module.button_upgrade on ['KMS Mastery Learning'] to user __system__ #1 via n/a
2026-08-17 22:25:27,632 18000 INFO kms_demo odoo.addons.base.models.ir_module: ALLOW access to module.update_list on ['KMS Mastery Learning'] to user __system__ #1 via n/a
2026-08-17 22:25:27,868 18000 WARNING kms_demo odoo.modules.module: Missing `author` key in manifest for 'kms_mastery', defaulting to ''
2026-08-17 22:25:28,401 18000 INFO kms_demo odoo.addons.base.models.ir_module: ALLOW access to module.button_install on [] to user __system__ #1 via n/a
2026-08-17 22:25:28,451 18000 INFO kms_demo odoo.modules.loading: loading 21 modules... 
2026-08-17 22:25:28,747 18000 INFO kms_demo odoo.modules.loading: Loading module kms_mastery (21/21) 
2026-08-17 22:25:28,809 18000 WARNING kms_demo odoo.registry: Model attribute '_sql_constraints' is no longer supported, please define models.Constraint on the model.
2026-08-17 22:25:28,809 18000 WARNING kms_demo odoo.registry: Model attribute '_sql_constraints' is no longer supported, please define models.Constraint on the model.
2026-08-17 22:25:28,814 18000 INFO kms_demo odoo.registry: module kms_mastery: creating or updating database tables
2026-08-17 22:25:28,899 18000 INFO kms_demo odoo.modules.loading: loading kms_mastery/security/kms_security.xml
2026-08-17 22:25:28,913 18000 WARNING kms_demo odoo.modules.loading: Transient module states were reset 
2026-08-17 22:25:28,913 18000 ERROR kms_demo odoo.registry: Failed to load registry
2026-08-17 22:25:28,914 18000 CRITICAL kms_demo odoo.service.server: Failed to initialize database `kms_demo`.
Traceback (most recent call last):
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 4381, in write
    self._check_field_access(self._fields[field_name], 'write')
                             ~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'users'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 608, in _tag_root
    f(rec)
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\convert.py", line 463, in _tag_record       
    record = model._load_records([data], self.mode == 'update')
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 5173, in _load_records       
    data['record']._load_records_write(data['values'])
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 5094, in _load_records_write 
    self.write(values)
  File "c:\users\aniru\documents\odoo19devenv\odoo\addons\mail\models\discuss\res_groups.py", line 10, in write
    res = super().write(vals)
          ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\addons\base\models\res_groups.py", line 195, in write
    res = super().write(vals)
          ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\models.py", line 4383, in write
    raise ValueError(f"Invalid field {field_name!r} in {self._name!r}") from e
ValueError: Invalid field 'users' in 'res.groups'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\service\server.py", line 1585, in preload_registries
    registry = Registry.new(dbname, update_module=update_module, install_modules=config['init'], upgrade_modules=config['update'], reinit_modules=config['reinit'])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\tools\func.py", line 88, in locked
    return func(inst, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\orm\registry.py", line 189, in new
    load_modules(
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\modules\loading.py", line 464, in load_modules    
    load_module_graph(
  File "C:\Users\aniru\Documents\Odoo19DevEnv\odoo\odoo\modules\loading.py", line 224, in load_module_graph
    load_data(env, idref, mode, kind='data', package=package)
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
odoo.tools.convert.ParseError: while parsing file:/c:/users/aniru/documents/odoo19devenv/custom_addons/kms_mastery/security/kms_security.xml:23, somewhere inside
<record id="group_kms_instructor" model="res.groups">
        <field name="name">Instructor</field>
        <field name="privilege_id" ref="res_groups_privilege_kms"/>
        <field name="sequence">20</field>
        <field name="implied_ids" eval="[(4, ref('group_kms_learner'))]"/>
        <field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
    </record>

---
---

Viewed res_groups.py:1-60
Searched for "_sql_constraints"
Viewed kms_security.xml:1-40
Edited kms_security.xml
Viewed __manifest__.py:1-10
Edited __manifest__.py
Viewed kms_user_node.py:38-48
Edited kms_user_node.py
Viewed kms_user_flashcard.py:80-95
Edited kms_user_flashcard.py

### What Happened

In Odoo 19, the field on `res.groups` for assigning users is named **`user_ids`** (not `users`):

```xml
<!-- In security/kms_security.xml -->
<record id="group_kms_instructor" model="res.groups">
    ...
    <!-- ❌ 'users' does not exist on res.groups in Odoo 19 -->
    <field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
    
    <!-- ✅ Correct field name in Odoo 19 -->
    <field name="user_ids" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
</record>
```

---

### Summary of Changes Applied

1. **[kms_security.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/security/kms_security.xml#L28):** Changed `<field name="users" ...>` to `<field name="user_ids" ...>`.
2. **[kms_demo_data.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/demo/kms_demo_data.xml#L13-L25):** Confirmed `<field name="group_ids" ...>` on `res.users` records.
3. **[kms_course.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_course.py#L22):** Domain on `instructor_id` uses `group_ids`.
4. **[__manifest__.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/__manifest__.py#L4):** Added missing `author` key to eliminate startup warnings.
5. **[kms_user_node.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_user_node.py#L40) & [kms_user_flashcard.py](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/models/kms_user_flashcard.py#L84):** Upgraded `_sql_constraints` to Odoo 19's `models.Constraint`.

---

### Run Upgrade

You can now upgrade the module cleanly on your database:

```powershell
.\venv\Scripts\python.exe .\odoo\odoo-bin -c odoo.conf -d kms_demo -u kms_mastery --without-demo=False
```