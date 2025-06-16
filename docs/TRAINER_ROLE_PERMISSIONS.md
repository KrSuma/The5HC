# Trainer Role Permissions Guide

## Role Hierarchy

The5HC uses a 4-tier role system for trainers within an organization:

### 1. Owner (소유자)
**Highest level of access**
- Can manage all trainers in the organization
- Can invite/remove trainers
- Can view all organization data and analytics
- Can access the organization dashboard
- Can edit organization settings
- Can deactivate other trainers (except other owners)
- Full access to all clients and assessments across the organization

### 2. Senior Trainer (시니어 트레이너)
**Management-level access**
- Can manage trainers (invite new trainers, view trainer list)
- Can access trainer management features
- Cannot access organization dashboard (owner-only)
- Cannot view organization-wide analytics
- Cannot edit organization settings
- Can only manage their own clients and assessments

### 3. Trainer (트레이너)
**Standard access**
- Can manage their own clients only
- Can create assessments for their clients
- Can manage sessions and payments for their clients
- Cannot invite or manage other trainers
- Cannot access trainer management features
- Standard trainer functionality without administrative privileges

### 4. Assistant (어시스턴트)
**Limited access**
- Most restricted role
- Can view and assist with client management
- Limited to basic trainer functions
- Cannot invite trainers or access management features
- Intended for junior staff or trainees

## Permission Methods

The Trainer model provides these permission check methods:

```python
is_owner()              # Returns True if role == 'owner'
is_senior()             # Returns True if role in ['owner', 'senior']
can_manage_trainers()   # Returns True if role in ['owner', 'senior']
can_view_all_data()     # Returns True if role == 'owner' (organization-wide data)
```

## View Access Control

### Owner-Only Views:
- Organization Dashboard (`/trainers/organization/dashboard/`)
- Organization Settings Edit

### Owner + Senior Views:
- Trainer Invite (`/trainers/invite/`)
- Trainer List Management
- Trainer Deactivation

### All Trainers:
- Own Profile Edit
- Client Management (own clients only)
- Assessment Management (own clients only)
- Session Management (own clients only)

## Data Isolation

- **Owners**: Can see all data across the organization
- **Senior/Trainer/Assistant**: Can only see data for their own clients
- Client ownership is enforced at the database query level
- Organization membership ensures trainers only see data within their organization

## Important Notes

1. A trainer can only belong to one organization (OneToOne relationship)
2. The first trainer in an organization is automatically set as the owner
3. Organizations have a max_trainers limit (default 50)
4. Deactivated trainers lose all access but their data is preserved
5. Role changes must be done by owners through the admin interface or database