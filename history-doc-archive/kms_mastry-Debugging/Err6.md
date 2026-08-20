## Troubleshoot DagViewer Props Error

UncaughtPromiseError > OwlError

Uncaught Promise > Invalid props for component 'DagViewer': unknown key 'action', unknown key 'actionId', unknown key 'updateActionState', unknown key 'className'

Occured on localhost:8069 on 2026-08-17 22:28:49 GMT

OwlError: Invalid props for component 'DagViewer': unknown key 'action', unknown key 'actionId', unknown key 'updateActionState', unknown key 'className'
    Error: Invalid props for component 'DagViewer': unknown key 'action', unknown key 'actionId', unknown key 'updateActionState', unknown key 'className'
        at Object.validateProps (http://localhost:8069/web/assets/59916d6/web.assets_web.min.js:996:67)
        at ControllerComponent.template (eval at compile (http://localhost:8069/web/assets/59916d6/web.assets_web.min.js:1383:421), <anonymous>:11:13)
        at Fiber._render (http://localhost:8069/web/assets/59916d6/web.assets_web.min.js:792:96)
        at Fiber.render (http://localhost:8069/web/assets/59916d6/web.assets_web.min.js:791:6)
        at ComponentNode.initiateRender (http://localhost:8069/web/assets/59916d6/web.assets_web.min.js:862:47)

---

Got this error on opening the DAG Viewer, investigate the cause

---
---

Searched for "DagViewer"
Viewed dag_viewer.js:1-60
Searched for "registry.category("actions")"
Searched for "static props"
Listed directory Odoo19DevEnv
Searched for "standardActionServiceProps"
Viewed action_service.js:80-110
Viewed dag_viewer.js:60-150
Searched for "dag_viewer"
Viewed kms_menus.xml:1-50
Searched for "useService("user")"
Searched for "user.userId"
Viewed user.js:1-60
Viewed dag_viewer.js:145-300
Viewed dag_viewer.js:301-485
Viewed dag_viewer.xml:1-50
Searched for "useService"
Searched for "Component"
Viewed __manifest__.py:1-49
Searched for "standardActionServiceProps"
Searched for "registry.category("actions").add"
Viewed view_hierarchy.js:1-45
Listed directory src
Listed directory components
Listed directory dag_viewer
Viewed dag_viewer.scss:1-50
Viewed kms_course_views.xml:1-60
Viewed kms_course_views.xml:61-148
Viewed kms_node_views.xml:1-60
Viewed kms_learner_views.xml:1-100
Viewed kms_menus.xml:80-119
Viewed dag_viewer.js:1-135
Edited dag_viewer.js
Viewed dag_viewer.js:1-60

### Cause of the Error

When `DagViewer` is registered and opened as a client action via `registry.category("actions").add("kms_mastery.dag_viewer", DagViewer)`, Odoo's action manager (`ActionContainer` / `action_service`) instantiates the component and injects standard action properties:
- `action` (the action descriptor object)
- `actionId`
- `className`
- `updateActionState`
- `globalState`
- `state`
- `resId`

In Owl, defining `static props = { ... }` enables strict prop validation. Because [dag_viewer.js](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/static/src/components/dag_viewer/dag_viewer.js) only declared:
```javascript
static props = {
    courseId: { type: Number, optional: true },
};
```
Owl rejected the undeclared standard client action properties (`action`, `actionId`, `updateActionState`, `className`) during render validation with:
`OwlError: Invalid props for component 'DagViewer': unknown key 'action', ...`

---

### Fix Applied

In [custom_addons/kms_mastery/static/src/components/dag_viewer/dag_viewer.js](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/static/src/components/dag_viewer/dag_viewer.js):

1. **Included Standard Action Props**:
   Imported `standardActionServiceProps` and spread it into `DagViewer.props`:
   ```javascript
   import { standardActionServiceProps } from "@web/webclient/actions/action_service";

   export class DagViewer extends Component {
       static template = "kms_mastery.DagViewer";
       static props = {
           ...standardActionServiceProps,
           courseId: { type: Number, optional: true },
       };
   ```

2. **Context-Aware Course & User Resolution**:
   - Added a `courseId` getter supporting both client action context (`props.action.context.active_id`) and direct component prop binding (`props.courseId`).
   - Injected the standard `user` service (`useService("user")`) for retrieving the active user ID.

---

### Verification / Next Step

Hard-refresh the browser page (`Ctrl + F5` or `Ctrl + Shift + R`) to load the updated asset bundle and open the **Knowledge DAG** menu again.

---
---

UncaughtPromiseError > OwlError

Uncaught Promise > An error occured in the owl lifecycle (see this Error's "cause" property)

Occured on localhost:8069 on 2026-08-17 22:36:32 GMT

OwlError: An error occured in the owl lifecycle (see this Error's "cause" property)
    Error: An error occured in the owl lifecycle (see this Error's "cause" property)
        at handleError (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:768:101)
        at App.handleError (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:1430:29)
        at Fiber._render (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:793:19)
        at Fiber.render (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:791:6)
        at ComponentNode.initiateRender (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:862:47)

Caused by: Error: Service user is not available
    at useService (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:4759:219)
    at DagViewer.setup (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:20266:772)
    at new ComponentNode (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:857:202)
    at http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:1428:6
    at ControllerComponent.template (eval at compile (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:1383:421), <anonymous>:12:27)
    at Fiber._render (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:792:96)
    at Fiber.render (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:791:6)
    at ComponentNode.initiateRender (http://localhost:8069/web/assets/30c6fe6/web.assets_web.min.js:862:47)

---

Got this error after updrading the module with the latest changes

---
---

Searched for "registry.category("services").add("user""
Searched for "import { user } from "@web/core/user""
Viewed dag_viewer.js:1-40
Viewed dag_viewer.js:120-145
Edited dag_viewer.js
Viewed dag_viewer.js:135-155
Edited dag_viewer.js
Viewed dag_viewer.js:1-40
Searched for "@odoo-module"
Edited dag_viewer.js
Viewed dag_viewer.js:1-70
Viewed dag_viewer.js:130-155

### Cause of the Error

In Odoo (including Odoo 19), `user` is not a registered dynamic service accessed via `useService("user")`. Calling `useService("user")` throws:
```
Error: Service user is not available
```
Instead, user session data is provided directly via the `@web/core/user` export.

---

### Fix Applied

In [custom_addons/kms_mastery/static/src/components/dag_viewer/dag_viewer.js](file:///c:/Users/aniru/Documents/Odoo19DevEnv/custom_addons/kms_mastery/static/src/components/dag_viewer/dag_viewer.js):

1. **Replaced `useService("user")` with Direct Module Import**:
   ```javascript
   import { user } from "@web/core/user";
   ```

2. **Updated `_getCurrentUserId()`**:
   ```javascript
   _getCurrentUserId() {
       return user.userId || odoo.session_info?.uid || 0;
   }
   ```
   and removed `this.user = useService("user");` from `setup()`.

---

### Next Steps

Hard-refresh the browser page (`Ctrl + F5` or `Ctrl + Shift + R`) to load the updated JavaScript bundle and click **Knowledge DAG**.