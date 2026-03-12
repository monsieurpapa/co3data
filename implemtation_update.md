# Cherry Register: ProductionRecord & Member Model Updates

## Background

The Excel file `20240714_TCC_Formualire de registre des cerises (1) (1).xlsx` is the **Formulaire de registre des cerises** (Cherry Register) used daily at washing stations. It captures **cherry deliveries** from individual farmers.

### Data discovered (1,293 records, station: KAHISA)

| Excel Column | Description | Maps To |
|---|---|---|
| Nom de la station de lavage | Washing station name | New `WashingStation` model |
| AAA ID Bio du fermier / Code Bio | Farmer code (e.g. `TCC BMB 009`) | `Member.farmer_code` |
| Nom du cafeiculteur | Farmer full name | `Member.first_name / last_name` |
| Groupement | Groupement (BUSHUMBA, MITI, MUDAKA) | `Member.groupement` (already exists) |
| Village du fermier | Village | `Member.village` (already exists) |
| Date d'achat | Purchase date at station | `ProductionRecord.purchase_date` |
| No de recu de paiement | Payment receipt number | `ProductionRecord.receipt_number` |
| Quantité cerise delivrée | Cherry quantity (kg) | `ProductionRecord.quantity_kg` (existing) |
| Prix de base (FC/unité) | Base price FC/unit | `ProductionRecord.base_price_fc` |
| Prix total | Total price (= qty × base price) | Computed property / stored |
| Taux de change Prix Café VS USD | FC → USD exchange rate | `ProductionRecord.exchange_rate_fc_usd` |
| No du registres de cerises | Cherry register number | `ProductionRecord.cherry_register_number` |
| No du rapport de livraison | Delivery report number | `ProductionRecord.delivery_report_number` |
| Date de reception a la station | Reception date at station | `ProductionRecord.reception_date` |

### Farmer Code Structure

```
TCC  BMB  009
 │    │    └── Sequential number within group (zero-padded 3-digit)
 │    └─────── Initials: Groupement initial (B=Bushumba, M=Miti/Mudaka) +
 │             SubGrouping initial + Village initial
 └──────────── Cooperative prefix (TCC = Trans-Coffee Cooperative?)
```

Examples decoded:
- `TCC BMB 009` → Bushumba / MUGANZO or CINJAVA → farmer #9  
- `TCC BIR 011` → Bushumba / ITARA → farmer #11  
- `TCC MCC 012` → Mudaka / CIFUMA → farmer #12  

The initials in the middle segment encode the groupement + village, not a strict 1:1 mapping (some codes appear across multiple villages), so we store the parsed parts for search/filtering but treat the full code as authoritative.

---

## Proposed Changes

### `cooperatives` Application

#### [MODIFY] [models.py](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py)

**`WashingStation` model (new)** — replaces hard-coded station name in the form:
```python
class WashingStation(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name="washing_stations")
    name = models.CharField(max_length=255)
    village = models.CharField(max_length=100, blank=True, null=True)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_active = models.BooleanField(default=True)
```

**[Member](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#28-81) model (enhanced):**
- Add `farmer_code` — full structured code `TCC BMB 009`, unique, indexed
- Add `subvillage` — sub-village / localité (more granular than village)
- Add `farmer_code_prefix`, `farmer_code_initials`, `farmer_code_number` — parsed segments stored for filtering/reporting
- Add [clean()](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#73-81) validator: parses and validates farmer code format (`^[A-Z]+ [A-Z]+ \d{3}$`)

**[ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) model (significantly enhanced):**
```
RECORD_TYPE_CHOICES: generic | cherry_delivery
```
New fields for cherry delivery context:
- `station` — FK to `WashingStation` (nullable for legacy generic records)
- `member` — FK to [Member](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#28-81) (direct; cherry goes station→member, not station→farm→member)
- `record_type` — `cherry_delivery` | `generic`
- `purchase_date` — date farmer brings cherries
- `receipt_number` — payment receipt number (CharField)
- `base_price_fc` — price per kg in Congolese Francs
- `total_price_fc` — stored computed field (qty × base_price, for offline availability)
- `exchange_rate_fc_usd` — FC→USD rate on purchase date
- `cherry_register_number` — register log number
- `delivery_report_number` — delivery report log number
- `reception_date` — date station received shipment
- `sync_uuid` — UUID field for offline-safe idempotency (auto-generated)
- `is_locally_created` — bool, True if created offline (for UI badge)
- Enhanced [clean()](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#73-81) — validates cherry_delivery requires station+member+receipt_number

> [!IMPORTANT]
> The existing `farm` FK on [ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) becomes nullable (`null=True, blank=True`) since cherry deliveries link directly to a [Member](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#28-81) (not a specific farm). Legacy generic records retain the farm FK.

#### [NEW] Migration file (auto-generated)
`src/cooperatives/migrations/0004_washingstation_productionrecord_cherry_fields_member_farmer_code.py`

---

### `sync` Application

#### [MODIFY] [models.py](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/sync/models.py)

**[PendingChange](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/sync/models.py#20-43)** — add `local_uuid` (UUID, unique) for idempotent replay. Without this, network retry on reconnection can create duplicate records.

**[SyncLog](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/sync/models.py#44-60)** — add `conflict_strategy` CharField (choices: `last_write_wins`, `server_wins`, `client_wins`, `manual`) to record which strategy was used during that sync session.

---

### Forms

#### [NEW] `cooperatives/forms.py` — `CherryDeliveryForm`
A Django ModelForm for [ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) with `record_type=cherry_delivery`, including:
- Station lookup (filtered to cooperative)
- Member lookup by `farmer_code` (autocomplete-ready)
- All cherry-specific fields with localized labels (FR)
- Auto-calculates `total_price_fc` on save

---

### Templates

#### [NEW] `templates/cooperatives/cherry_delivery_form.html`
Form view for offline-capable cherry delivery entry (HTML5 form with service worker cache header hints).

#### [NEW] `templates/cooperatives/cherry_delivery_list.html`
List view showing all cherry deliveries with filter by station, date, member code, and sync status badge (🟡 pending / 🟢 synced).

---

### Views & URLs

#### [MODIFY] `cooperatives/views.py`
Add class-based views:
- `CherryDeliveryListView` — filterable list
- `CherryDeliveryCreateView` — with offline-queuing on submit
- `CherryDeliveryDetailView`

#### [MODIFY] `cooperatives/urls.py`
Wire `/cherry-deliveries/`, `/cherry-deliveries/new/`, `/cherry-deliveries/<pk>/`.

---

### Admin

#### [MODIFY] `cooperatives/admin.py`
Register `WashingStation` with inline for [ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) cherry deliveries.
Update [ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) admin with fieldsets separating generic vs cherry delivery fields.

---

## User Review Required

> [!IMPORTANT]
> **`farm` FK becomes nullable.** Existing [ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) rows with a `farm` have `farm_id` set. After migration, new cherry delivery records will have `farm=NULL` and `member` set instead. This is intentional — cherry deliveries at a washing station are member-level events, not farm-level. Please confirm this is acceptable.

> [!WARNING]
> **`member_id` uniqueness scope.** Currently `Member.member_id` is unique per [(cooperative, member_id)](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#65-69). The new `farmer_code` field (e.g., `TCC BMB 009`) will be **globally unique** across cooperatives since it already embeds the cooperative prefix. We set `farmer_code` with `unique=True` at the model level. If the same code exists for a different cooperative that's a data issue in the source. Please confirm.

---

## Verification Plan

### Automated (run after execution)
```powershell
# In src/
python manage.py makemigrations cooperatives sync --check   # expect new migrations
python manage.py makemigrations cooperatives sync           # generate migrations
python manage.py migrate                                    # apply, expect no errors
python manage.py check                                      # expect "System check identified no issues"
```

### Manual Verification
1. Open Django admin → confirm `WashingStation`, [ProductionRecord](file:///c:/Users/Yves%20Zigashane/Documents/Projects/co3data/src/cooperatives/models.py#97-124) (with new fields) appear
2. Enter one cherry delivery record for farmer `TCC BMB 009` (Bulonza MUDUMBI) at station KAHISA, date 2024-04-06, qty 56 kg, price 1000 FC, receipt 8957, register 14002, report 5251
3. Check that `total_price_fc` = 56,000 FC is auto-calculated
4. Check that `sync_uuid` is auto-populated (UUID)
5. Confirm `Member.farmer_code` field accepts `TCC BMB 009` and rejects `INVALID-CODE`
