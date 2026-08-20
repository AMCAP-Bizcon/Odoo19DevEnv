## Odoo Module Installation Error

2026-08-17 21:48:44,505 25136 INFO kms_demo odoo.registry: module kms_mastery: creating or updating database tables
2026-08-17 21:48:45,469 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/security/kms_security.xml
2026-08-17 21:48:45,602 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/security/ir.model.access.csv
2026-08-17 21:48:45,652 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/data/mail_template_data.xml
2026-08-17 21:48:45,669 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/data/ir_cron_data.xml
2026-08-17 21:48:45,722 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_quiz_views.xml
2026-08-17 21:48:45,800 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_flashcard_views.xml
2026-08-17 21:48:45,835 25136 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_node_views.xml
2026-08-17 21:48:45,964 25136 WARNING kms_demo odoo.modules.loading: Transient module states were reset 
2026-08-17 21:48:45,964 25136 ERROR kms_demo odoo.registry: Failed to load registry 
2026-08-17 21:48:45,964 25136 CRITICAL kms_demo odoo.service.server: Failed to initialize database `kms_demo`.
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
odoo.tools.convert.ParseError: while parsing file:/c:/users/aniru/documents/odoo19devenv/custom_addons/kms_mastery/views/kms_node_views.xml:35
Error while validating view near:

<form string="Knowledge Node" __validate__="1">
                <sheet>
                    <div class="oe_button_box" name="button_box">

<b>Access Rights Inconsistency</b><br/>This view may not work for all users: some users may have a combination of groups where the elements <b><tt>&lt;button&gt;</tt></b> are displayed, but they depend on the field <b><tt>active_id</tt></b> that is not accessible. You might fix this by modifying user groups to make sure that all users who have access to those elements also have access to the field, typically via group implications. Alternatively, you could adjust the “<i>groups</i>” or “<i>invisible</i>” attributes for these fields, to make sure they are always available together.<br/>Debugging information:<br/>- field “active_id” does not exist in model “kms.node”.<br/>- element “&lt;button class=&#34;oe_stat_button&#34; icon=&#34;fa-clone&#34; name=&#34;146&#34; type=&#34;action&#34; context=&#34;{&#39;default_node_id&#39;: active_id, &#39;search_default_node_id&#39;: active_id}&#34;/&gt;” is shown in the view for groups: &#39;kms_mastery.group_kms_learner&#39;

View error context:
{'file': 'c:\\users\\aniru\\documents\\odoo19devenv\\custom_addons\\kms_mastery\\views\\kms_node_views.xml',
 'line': 1,
 'name': 'kms.node.view.form',
 'view': ir.ui.view(426,),
 'view.model': 'kms.node',
 'view.parent': ir.ui.view(),
 'xmlid': 'kms_node_view_form'

---

Above is the error log recieved while trying to install custom_addons\kms_mastery, find the root cause

---
---

Viewed kms_node_views.xml:1-121
Edited kms_node_views.xml

The root cause of the error is that you are using `active_id` within the `context` attribute of the stat buttons in your form view for `kms.node`. 

In newer versions of Odoo (especially 16+), the view validator evaluates the `context` string against the fields of the current model. Since `active_id` is not an actual field on the `kms.node` model, the validator assumes it could lead to access right inconsistencies and throws a `ParseError`.

To fix this, you should use `id` instead of `active_id` to refer to the current record's ID inside a form view. 

I've gone ahead and fixed this for you by modifying [kms_node_views.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/views/kms_node_views.xml) and updating the contexts to:
```xml
context="{'default_node_id': id, 'search_default_node_id': id}"
```

You can now restart your Odoo server and try installing/upgrading the module again. It should work perfectly!

Viewed kms_node_views.xml:1-26

---
---

2026-08-17 22:04:15,739 33040 INFO kms_demo odoo.registry: module kms_mastery: creating or updating database tables
2026-08-17 22:04:16,862 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/security/kms_security.xml
2026-08-17 22:04:17,103 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/security/ir.model.access.csv
2026-08-17 22:04:17,142 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/data/mail_template_data.xml
2026-08-17 22:04:17,173 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/data/ir_cron_data.xml
2026-08-17 22:04:17,245 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_quiz_views.xml
2026-08-17 22:04:17,362 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_flashcard_views.xml
2026-08-17 22:04:17,389 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_node_views.xml
2026-08-17 22:04:17,436 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_milestone_views.xml
2026-08-17 22:04:17,490 33040 INFO kms_demo odoo.modules.loading: loading kms_mastery/views/kms_course_views.xml
2026-08-17 22:04:17,621 33040 WARNING kms_demo odoo.modules.loading: Transient module states were reset 
2026-08-17 22:04:17,621 33040 ERROR kms_demo odoo.registry: Failed to load registry 
2026-08-17 22:04:17,625 33040 CRITICAL kms_demo odoo.service.server: Failed to initialize database `kms_demo`.
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
odoo.tools.convert.ParseError: while parsing file:/c:/users/aniru/documents/odoo19devenv/custom_addons/kms_mastery/views/kms_course_views.xml:37
Error while validating view near:

<form string="Course" __validate__="1">
                <sheet>
                    <div class="oe_button_box" name="button_box">

<b>Access Rights Inconsistency</b><br/>This view may not work for all users: some users may have a combination of groups where the elements <b><tt>&lt;button&gt;</tt></b> are displayed, but they depend on the field <b><tt>active_id</tt></b> that is not accessible. You might fix this by modifying user groups to make sure that all users who have access to those elements also have access to the field, typically via group implications. Alternatively, you could adjust the “<i>groups</i>” or “<i>invisible</i>” attributes for these fields, to make sure they are always available together.<br/>Debugging information:<br/>- field “active_id” does not exist in model “kms.course”.<br/>- element “&lt;button name=&#34;151&#34; type=&#34;action&#34; class=&#34;oe_stat_button&#34; icon=&#34;fa-sitemap&#34; context=&#34;{&#39;default_course_id&#39;: active_id}&#34;/&gt;” is shown in the view for groups: &#39;kms_mastery.group_kms_learner&#39;

View error context:
{'file': 'c:\\users\\aniru\\documents\\odoo19devenv\\custom_addons\\kms_mastery\\views\\kms_course_views.xml',
 'line': 1,
 'name': 'kms.course.view.form',
 'view': ir.ui.view(447,),
 'view.model': 'kms.course',
 'view.parent': ir.ui.view(),
 'xmlid': 'kms_course_view_form'}

---

I guess the error persists ever after the previous change

---
---

Searched for "active_id"
Viewed kms_course_views.xml:35-65
Searched for "context=""
Viewed kms_course_views.xml:1-148
Searched for "course_id"
Viewed kms_course.py:1-60
Viewed kms_node.py:1-60
Viewed kms_node.py:60-87
Searched for "<button"
Viewed __manifest__.py:1-48
Viewed kms_learner_views.xml:1-200
Viewed kms_learner_views.xml:201-260
Viewed kms_menus.xml:1-119
Edited kms_course_views.xml
Searched for "active_id"

The previous fix actually **did resolve** the error in [kms_node_views.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/views/kms_node_views.xml)! 

If you look at the loading sequence in your new log:
```text
loading kms_mastery/views/kms_node_views.xml      <-- Succeeded!
loading kms_mastery/views/kms_milestone_views.xml <-- Succeeded!
loading kms_mastery/views/kms_course_views.xml    <-- Failed here
```

The error occurred in the next file: [kms_course_views.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/views/kms_course_views.xml). It had the exact same issue on line 48:
```xml
<button name="%(kms_mastery.kms_node_action)d"
        type="action"
        class="oe_stat_button"
        icon="fa-sitemap"
        context="{'default_course_id': active_id}">
    <field name="node_count" widget="statinfo" string="Nodes"/>
</button>
```

### What was causing it & the fix:
1. **`active_id` View Validation**: The view validator failed because `active_id` is evaluated against the model's fields (`kms.course`), where `active_id` does not exist.
2. **Relational Structure**: `kms.node` and `kms.course` are related via a Many2many field (`node_ids` on `kms.course`), meaning `kms.node` doesn't have a `course_id` field anyway. To filter the nodes belonging to the course when clicking the stat button, `domain="[('id', 'in', node_ids)]"` should be used.

### Changes Made:
In [kms_course_views.xml](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/views/kms_course_views.xml), updated the stat button to:
```xml
<button name="%(kms_mastery.kms_node_action)d"
        type="action"
        class="oe_stat_button"
        icon="fa-sitemap"
        domain="[('id', 'in', node_ids)]">
    <field name="node_count" widget="statinfo" string="Nodes"/>
</button>
```

I have also verified across the entire addon that there are no remaining occurrences of `active_id`. You can now restart your Odoo server and reinstall/upgrade the module.