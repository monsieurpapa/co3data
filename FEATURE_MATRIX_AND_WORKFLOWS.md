# CO3DATA Feature Matrix & User Workflows

## Role-Based Feature Access Matrix

### Legend:
- ✅ Full Access (View + Create + Edit + Delete)
- 👁️ View Only
- ➕ Create & Edit
- ❌ No Access
- 🔒 Admin Only

| Feature | Member | Manager | Regional Officer | Apex Body | Government | Admin |
|---------|--------|---------|-----------------|-----------|-----------|-------|
| **Cooperatives** |
| View List | 👁️ | 👁️ | <ul><li>✅</li></ul> | 👁️ | 👁️ | ✅ |
| View Detail | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |
| Create | ❌ | ❌ | ➕ | ❌ | ❌ | ✅ |
| Edit | ❌ | ➕ | ➕ | ❌ | ❌ | ✅ |
| Delete | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| **Members** |
| View List | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |
| View Detail | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |
| Create | ❌ | ➕ | ➕ | ❌ | ❌ | ✅ |
| Edit | ❌ | ➕ | ➕ | ❌ | ❌ | ✅ |
| Delete | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Cherry Deliveries** |
| View List | 👁️ | ✅ | ✅ | ❌ | 👁️ | ✅ |
| View Detail | 👁️ | ✅ | ✅ | ❌ | 👁️ | ✅ |
| Create | ❌ | ➕ | ➕ | ❌ | ❌ | ✅ |
| Edit | ❌ | ➕ | ➕ | ❌ | ❌ | ✅ |
| Delete | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Questionnaires** |
| View List | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Detail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Create | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Edit | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| **Submissions** |
| View List | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| View Detail | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Users** (Admin Only) |
| View List | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Create User | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Edit User | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Delete User | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| **Organizations** (Admin Only) |
| View List | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Create Org | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Edit Org | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |
| Delete Org | ❌ | ❌ | ❌ | ❌ | ❌ | 🔒 |

## User Workflow Examples

### Workflow 1: Regional Officer Registering a New Cooperative

```
1. Login as Regional Officer
2. Navigate to: Coopératives (sidebar) → "Nouvelle Coopérative" button
3. Fill in form:
   - Name: COOP-KASAI-001
   - Type: Coffee Cooperative
   - Region: Kasai
   - Registration Number: REG-2024-001
   - Contact Person: Joseph N'Dombe
   - Establishment Date: 2024-01-15
   - Address: Kasai Region, DRC
4. Click "Créer la Coopérative" button
5. System confirms: "Coopérative créée avec succès"
6. Page redirects to cooperative list
7. New cooperative appears in list
8. Can now manage members and collect data
```

### Workflow 2: Manager Adding a New Cooperative Member

```
1. Login as Manager
2. Navigate to: Coopératives → Select cooperative → View members section
   OR Direct: Membres list
3. Click "Ajouter un Membre" button
4. Fill form:
   - Cooperative: Select from dropdown
   - Name: Jean Pierre Mwamba
   - Member ID: COOP-JP-001
   - Gender: Male
   - Age Group: 35-44
   - Phone: +243700123456
   - Farmer Code: JP-001-2024
   - Is Marginalized: ☐ (unchecked)
   - Is Board Member: ☑ (checked)
   - Board Role: Treasurer
5. Click "Créer le Membre" button
6. System confirms: "Membre créé avec succès"
7. Member appears in list with appropriate badges
```

### Workflow 3: Recording a Cherry Delivery

```
1. Login as Manager or Regional Officer
2. Navigate to: Livraisons de Cerises
3. Click "Nouvelle livraison" button
4. Fill Section 1 - Informations de Livraison:
   - Station: Select washing station
   - Member: Select farmer/member
5. Fill Section 2 - Dates & Quantités:
   - Purchase Date: 2024-03-12
   - Reception Date: 2024-03-13
   - Quantity (kg): 150
6. Fill Section 3 - Tarification:
   - Base Price (FC): 2500
   - Total Price: 375000 (auto-calculated)
   - Exchange Rate (FC/USD): 3000
7. Fill Section 4 - Numéros de Registre:
   - Receipt Number: REC-2024-001
   - Cherry Register Number: CR-2024-001
   - Delivery Report Number: DR-2024-001
8. Click "Enregistrer la Livraison" button
9. System confirms: "Livraison enregistrée avec succès"
10. Delivery appears in list with "Synchronisé" status
11. Can now view, edit, or delete if needed
```

### Workflow 4: Completing a Questionnaire Submission

```
1. Login as any cooperative member
2. Navigate to: Questionnaires list
3. See available questionnaires for data collection
4. Click on questionnaire (e.g., "Financial Health Assessment")
5. Click "Répondre" button
6. System displays:
   - Questionnaire title and description
   - Target object (e.g., Cooperative: COOP-KASAI-001)
   - Questions to answer
7. Fill responses:
   - Question 1: Type response
   - Question 2: Select from dropdown
   - Question 3: Enter number
   - ... (repeat for all questions)
8. Click "Envoyer la réponse" button
9. System confirms: "Soumission enregistrée avec succès"
10. Redirects to submissions list
11. Submission appears in history with timestamp and submitter name
```

### Workflow 5: Administrator Managing Users

```
1. Login as Admin/Superuser
2. Navigate to: Admin → Utilisateurs
3. View all users in system
4. To Create New User:
   - Click "Ajouter un Utilisateur"
   - Fill: Username, Email, First Name, Last Name, Password
   - Assign: Organization, Role
   - Click "Créer l'Utilisateur"
5. To Edit User:
   - Click dropdown menu (three dots) → "Modifier"
   - Update fields as needed
   - Click "Enregistrer les modifications"
6. To View User Details:
   - Click dropdown menu → "Voir"
   - View read-only information
7. To Delete User:
   - Click dropdown menu → "Supprimer"
   - Confirm on delete page
   - User removed from system
```

### Workflow 6: Viewing Analytics & Data

```
1. Login as any authorized user
2. Click "Accueil" (Dashboard) in sidebar
3. View key metrics:
   - Pending entries (if applicable)
   - Recent submissions
   - Cooperative statistics
4. Navigate to specific modules:
   - Coopératives: View cooperative list
   - Membres: View member list
   - Livraisons: View delivery records
   - Soumissions: View questionnaire submissions
5. Use filters to drill down:
   - By Region (if view allows)
   - By Status
   - By Date Range
6. Click on item to view details
7. Select "Voir" action to view full record
```

## Data Model Relationships

```
Organization (1)
    ↓
    └─→ User (Many)
            └─→ Region (1)
                    └─→ Cooperative (Many)
                            ├─→ WashingStation (Many)
                            ├─→ Member (Many)
                            │   ├─→ ProductionRecord/Cherry Delivery (Many)
                            │   └─→ Submission (Many - via GenericFK)
                            └─→ Submission (Many - via GenericFK)
                                    ├─→ Questionnaire (1)
                                    │   └─→ Question (Many)
                                    └─→ Answer (Many)
```

## Key Features by Module

### Cooperatives Module
- **Purpose:** Manage cooperative organizations
- **Key Actions:** Register, update, delete cooperatives
- **Key Data:** Name, type, region, registration number, contact person
- **Integration:** Gateway to members and delivery records

### Members Module
- **Purpose:** Track individual cooperative members
- **Key Actions:** Register, update, delete members
- **Key Data:** Demographics, farmer code, status (board, marginalized)
- **Integration:** Links to cooperatives and production records

### Cherry Deliveries Module
- **Purpose:** Record cherry/cocoa deliveries to washing stations
- **Key Actions:** Record, update, delete deliveries
- **Key Data:** Date, quantity, price, receipt numbers, sync status
- **Integration:** Links to members and washing stations

### Questionnaires Module
- **Purpose:** Dynamic data collection
- **Key Actions:** Submit responses, view submissions, view questionnaire details
- **Key Data:** Questions, answer types, target models
- **Integration:** Collects data about cooperatives and members

### Submissions Module
- **Purpose:** Track questionnaire response history
- **Key Actions:** View submissions, see response details
- **Key Data:** Submitted by, submission date, questionnaire, target
- **Integration:** Part of questionnaire workflow

## API Endpoints (REST)

Available for integration:
- `/api/cooperatives/` - Cooperative CRUD
- `/api/members/` - Member CRUD
- `/api/farms/` - Farm data (if applicable)
- `/api/production-records/` - Production record CRUD
- Documentation: See `docs/API.md`

## Screen Flow Diagram

```
Login Page
    ↓
Dashboard
    ├─→ Coopératives List
    │   ├─→ Cooperative Detail
    │   │   ├─→ Edit Form
    │   │   ├─→ Delete Confirm
    │   │   └─→ Members Section
    │   │       └─→ Member List
    │   │           ├─→ Member Detail
    │   │           ├─→ Edit Form
    │   │           └─→ Delete Confirm
    │   └─→ Create Form
    │
    ├─→ Membres List
    │   ├─→ Member Detail
    │   ├─→ Edit Form
    │   └─→ Delete Confirm
    │
    ├─→ Livraisons List
    │   ├─→ Delivery Detail
    │   ├─→ Edit Form
    │   └─→ Delete Confirm
    │
    ├─→ Questionnaires List
    │   ├─→ Questionnaire Detail
    │   └─→ Submission Form
    │
    ├─→ Soumissions List
    │   └─→ Submission Detail
    │
    └─→ Admin (Superuser only)
        ├─→ Users Management
        └─→ Organizations Management
```

## Performance Optimizations

- **Pagination:** 20 items per page on list views
- **Lazy Loading:** Member counts calculated on-demand
- **Caching:** Region and organization caching recommended
- **Indexing:** Foreign key fields indexed for fast filtering

## Internationalization (i18n)

All templates support multiple languages via `{% trans %}` tags:
- **Primary:** French (fr)
- **Secondary:** English (en)
- **Extensible:** Add new language files as needed

Current translations cover:
- UI labels and buttons
- Error messages
- Help text
- Field labels
- Status messages
