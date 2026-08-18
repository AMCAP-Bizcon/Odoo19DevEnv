---
trigger: always_on
---

# Odoo 19 Coding Guidelines & Best Practices

Based on debugging logs and errors encountered during the development of Odoo 19 custom modules, this reference serves as a guide for coding agents to avoid repeating common mistakes. Odoo 19 introduces several strict validations and architectural changes.

## 1. Security and Access Rights

### 1.1 `res.groups` Category Link (`res.groups.privilege`)
**Error:** `ValueError: Invalid field 'category_id' in 'res.groups'`
- **Odoo 19 Change:** The `category_id` field has been removed from `res.groups`. Instead, Odoo 19 uses an intermediate model `res.groups.privilege`.
- **Solution:** Create a `res.groups.privilege` record under your category, and link your `res.groups` to it using the `privilege_id` field.
```xml
<!-- Group Privilege -->
<record id="res_groups_privilege_kms" model="res.groups.privilege">
    <field name="name">KMS Mastery</field>
    <field name="category_id" ref="module_category_kms"/>
</record>

<!-- Security Group -->
<record id="group_kms_learner" model="res.groups">
    <field name="name">Learner</field>
    <field name="privilege_id" ref="res_groups_privilege_kms"/>
</record>
```

### 1.2 `res.users` Groups Field
**Error:** `ValueError: Invalid field 'groups_id' in 'res.users'`
- **Odoo 19 Change:** The Many2many field on `res.users` for assigning security groups has been renamed from `groups_id` to **`group_ids`**.

### 1.3 `res.groups` Users Field
**Error:** `ValueError: Invalid field 'users' in 'res.groups'`
- **Odoo 19 Change:** The field on `res.groups` for assigning users has been renamed from `users` to **`user_ids`**.

---

## 2. Views and XML Validation

### 2.1 Search View `<group>` Attributes
**Error:** `Invalid view ... definition ... Error while validating view`
- **Odoo 19 Change:** The search view schema (relaxng validation) no longer supports the `expand="0"` or `string="Group By"` attributes on the `<group>` tag inside a `<search>` element.
- **Solution:** Use a simple `<group>` tag without these attributes.
```xml
<!-- ❌ Invalid -->
<group expand="0" string="Group By"> 
    <filter string="Instructor" name="group_instructor" context="{'group_by': 'instructor_id'}"/>
</group>

<!-- ✅ Valid -->
<group> 
    <filter string="Instructor" name="group_instructor" context="{'group_by': 'instructor_id'}"/>
</group>
```

### 2.2 `active_id` in Form View Contexts/Domains
**Error:** `Access Rights Inconsistency ... field “active_id” does not exist in model`
- **Odoo 19 Change:** The view validator strictly evaluates the `context` and `domain` strings against the fields of the current model. Since `active_id` is not an actual field on the model, it causes a `ParseError`.
- **Solution:** Use `id` instead of `active_id` to refer to the current record's ID inside a form view button. (e.g., `context="{'default_node_id': id}"`)

### 2.3 XML File Loading Order
- **Rule:** If a view references an action (e.g., in a stat button like `name="%(my_module.my_action)d"`), the XML file defining that action **must** be loaded before the view referencing it in the `__manifest__.py` data array. Otherwise, it will cause an "External ID not found" error.

---

## 3. Python Backend

### 3.1 Dynamic Domains in Python Fields
**Error:** `ParseError: Invalid view ... definition` caused by syntax error in Python model.
- **Rule:** The syntax `%(module.xml_id)d` is **only valid inside XML files**. If you need to reference an XML ID in a Python field definition (like a domain), you must use a `lambda` function.
```python
# ❌ Invalid Python domain
domain="[('group_ids', 'in', %(kms_mastery.group_kms_instructor)d)]"

# ✅ Valid Python domain
domain=lambda self: [('group_ids', 'in', self.env.ref('kms_mastery.group_kms_instructor').id)]
```

### 3.2 SQL Constraints
**Warning:** `Model attribute '_sql_constraints' is no longer supported`
- **Odoo 19 Change:** The traditional `_sql_constraints` list on models is deprecated.
- **Solution:** Use `models.Constraint` objects to define database constraints.

---

## 4. Frontend (OWL & JavaScript)

### 4.1 Client Action Components & Strict Props
**Error:** `OwlError: Invalid props for component 'MyComponent': unknown key 'action', ...`
- **Odoo 19 Rule:** When an OWL component is registered as a client action, Odoo's action manager injects standard properties (`action`, `actionId`, `className`, etc.). If your component uses strict prop validation (`static props = { ... }`), it will reject these and crash.
- **Solution:** Import and spread `standardActionServiceProps`.
```javascript
import { Component } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class MyActionComponent extends Component {
    static props = {
        ...standardActionServiceProps,
        myCustomProp: { type: Number, optional: true },
    };
}
```

### 4.2 Accessing User Session
**Error:** `Error: Service user is not available`
- **Odoo 19 Rule:** The active user session is not available as a standard dynamic service (you cannot use `useService("user")`). 
- **Solution:** Import the `user` object directly from `@web/core/user`.
```javascript
// ❌ Invalid
const user = useService("user");

// ✅ Valid
import { user } from "@web/core/user";
const currentUserId = user.userId;
```

---

## 5. General Tips

### 5.1 Demo Data Failures Are Silent
- **Rule:** Odoo wraps demo data loading in a `try...except` savepoint. If an error occurs in your `demo.xml` data, Odoo will rollback the transaction, print a warning to the logs, and **silently continue installing the module**. 
- Always check the server logs for `Module <name> demo data failed to install` if your demo data does not appear.

### 5.2 Manifest Structure
- **Rule:** Ensure your `__manifest__.py` contains the `author` key, even if empty, to avoid startup warnings (`Missing 'author' key in manifest`).
