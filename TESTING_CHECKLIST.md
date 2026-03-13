# CO3DATA CRUD & UI/UX Testing Checklist

## Pre-Launch Testing

### 1. **User List Tests**
- [ ] Navigate to Users list page
- [ ] Verify dropdown actions appear for each user
- [ ] Click "Voir" to view user details
- [ ] Click "Modifier" to edit user
- [ ] Click "Supprimer" to delete user (should show confirmation)
- [ ] Verify only superusers can see user management
- [ ] Check responsive design on mobile

### 2. **Cooperative List Tests**
- [ ] Navigate to Coopératives list
- [ ] Verify "Nouvelle Coopérative" button visible for authorized roles
- [ ] Test dropdown actions (view, edit, delete)
- [ ] Verify member count displays correctly
- [ ] Verify role-based permission checks (admin, regional_officer, manager)
- [ ] Test search/filter functionality

### 3. **Member List Tests**
- [ ] Navigate to Membres list
- [ ] Verify dropdown menu with actions
- [ ] Check badges display (gender, age group, marginalized, board member)
- [ ] Verify edit/delete permissions by role
- [ ] Test pagination if > 20 members
- [ ] Verify inline filtering by cooperative

### 4. **Cherry Delivery Tests**
- [ ] Navigate to Livraisons de Cerises
- [ ] Verify new "Nouvelle livraison" button works
- [ ] Check dropdown actions on each delivery
- [ ] Click "Voir Détails" to check detail page
- [ ] Click "Modifier" to edit delivery (test form improvements)
- [ ] Click "Supprimer" to delete (test new delete confirmation template)
- [ ] Verify sync status badge (En attente vs Synchronisé)
- [ ] Test all filters (station, farmer_code, date range, sync status)

### 5. **Cherry Delivery Form Tests** ⭐ Critical
- [ ] Load create new delivery form
- [ ] Verify form fields are grouped logically
- [ ] Test all form validations
- [ ] Verify date pickers work
- [ ] Verify dropdown selects work (station, member)
- [ ] Submit form and verify success
- [ ] Test form with missing required fields (should show errors)
- [ ] Load edit delivery form
- [ ] Verify all fields populate with existing data
- [ ] Modify and save (verify update works)
- [ ] Test breadcrumb navigation

### 6. **Questionnaire Tests**
- [ ] Navigate to Questionnaires list
- [ ] Verify dropdown actions work
- [ ] Click "Voir" to view questionnaire details
- [ ] Click "Modifier" (admin only feature)
- [ ] Check status badge (Public vs Brouillon)

### 7. **Submission Tests**
- [ ] Navigate to Submissions list
- [ ] Verify improved table layout
- [ ] Click "Voir les réponses" to view submission details
- [ ] Verify no edit/delete buttons (read-only by design)
- [ ] Check submitted_by and submitted_at display correctly

### 8. **Organization Tests**
- [ ] Navigate to Organizations list
- [ ] Verify "Nouvelle Organisation" button works
- [ ] Test dropdown actions (Modifier, Supprimer)
- [ ] Verify Active/Inactive status badge displays
- [ ] Verify unique code badge displays

### 9. **Permission Tests**
- [ ] Login as admin → verify full access
- [ ] Login as regional_officer → verify limited options
- [ ] Login as manager → verify limited options
- [ ] Login as regular member → verify view-only or restricted access
- [ ] Verify "Supprimer" button only shows for authorized roles
- [ ] Verify "Modifier" button shows based on role

### 10. **Responsive Design Tests**
- [ ] Test on Desktop (1920x1080)
- [ ] Test on Tablet (768x1024)
- [ ] Test on Mobile (375x667)
- [ ] Verify table scrolls horizontally on mobile
- [ ] Verify dropdown menus work on touch
- [ ] Verify forms are readable on all sizes
- [ ] Check button sizes are adequate for touch (min 44px)

### 11. **Navigation Tests**
- [ ] Verify breadcrumb navigation on all detail pages
- [ ] Verify "Retour" buttons go to correct list page
- [ ] Verify "Annuler" buttons don't save data
- [ ] Check back button functionality
- [ ] Verify links in dropdown menus work

### 12. **Form Validation Tests**
- [ ] Test required fields validation
- [ ] Test email format validation (if applicable)
- [ ] Test number field validation
- [ ] Test date field validation
- [ ] Verify error messages display properly
- [ ] Verify form clears after successful submission (create only)
- [ ] Test inline error indicators

### 13. **Data Display Tests**
- [ ] Verify all columns display correctly in lists
- [ ] Verify table sorting works (if enabled)
- [ ] Verify badge colors are appropriate
- [ ] Verify icons display correctly
- [ ] Verify empty state messages display ("Aucun... trouvé")
- [ ] Verify dates are formatted consistently (d/m/Y)

### 14. **Accessibility Tests**
- [ ] Test keyboard navigation (Tab, Enter, Escape)
- [ ] Verify focus indicators visible on buttons
- [ ] Test screen reader compatibility (if possible)
- [ ] Verify color contrast meets WCAG standards
- [ ] Test form labels are properly associated with inputs
- [ ] Verify dropdown menus can be closed with Escape key

### 15. **Performance Tests**
- [ ] Verify page load times acceptable
- [ ] Check for console errors in browser dev tools
- [ ] Verify images load properly (if any)
- [ ] Test with slow network (throttle in dev tools)
- [ ] Verify no duplicate/missing CSS classes

## Test Environment Setup

```bash
# Install test requirements
pip install -r requirements.txt

# Run Django tests
python src/manage.py test

# Load test data
python src/manage.py populate_test_data

# Start development server
python src/manage.py runserver 0.0.0.0:8000

# Visit test pages
- http://localhost:8000/users/list/
- http://localhost:8000/cooperatives/list/
- http://localhost:8000/cooperatives/members/
- http://localhost:8000/cooperatives/cherry-deliveries/
- http://localhost:8000/admin/organizations/
```

## User Roles for Testing

1. **Superuser/Admin**
   - Username: admin
   - Can access all CRUD operations
   - Can manage users and organizations

2. **Regional Officer**
   - Can view and edit cooperatives
   - Can view and edit members
   - Cannot delete

3. **Manager**
   - Can view and edit members
   - Can delete members
   - Limited to assigned cooperative

4. **Standard Member**
   - View-only access to most data
   - Can submit questionnaires

## Known Issues to Check

- [ ] Cherry delivery form fields align properly in all screen sizes
- [ ] Dropdown menus don't overflow on small screens
- [ ] Delete confirmation modal displays correctly
- [ ] Pagination works with filters applied
- [ ] Form resubmission protection (if applicable)

## Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Firefox Mobile
- [ ] Chrome Mobile

## Final Approval Checklist

Before marking as complete:
- [ ] All tests pass
- [ ] No console errors
- [ ] Responsive on all devices
- [ ] All CRUD operations work
- [ ] Permissions enforced correctly
- [ ] Help content visible and useful
- [ ] Forms validate properly
- [ ] Navigation flows logically
- [ ] Data displays correctly
- [ ] No missing translations

## Sign-Off

- QA Tester: _________________ Date: _______
- Product Owner: _________________ Date: _______
- Technical Lead: _________________ Date: _______
