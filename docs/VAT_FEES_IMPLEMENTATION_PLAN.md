# VAT and Card Processing Fees Implementation Plan

## Executive Summary

This document outlines the implementation plan for adding VAT (부가세) and card processing fee (카드 수수료) breakdown to the package management UI. The solution maintains backward compatibility while providing transparent fee calculations and comprehensive audit trails.

## Table of Contents

1. [Database Schema Modifications](#database-schema-modifications)
2. [Payment Processing Flow](#payment-processing-flow)
3. [VAT/Fee Calculation Logic](#vatfee-calculation-logic)
4. [UI Display Updates](#ui-display-updates)
5. [Migration Strategy](#migration-strategy)
6. [Technical Considerations](#technical-considerations)
7. [Testing Scenarios](#testing-scenarios)
8. [Implementation Timeline](#implementation-timeline)

## Database Schema Modifications

### 1. Enhanced session_packages Table

```sql
ALTER TABLE session_packages ADD COLUMN gross_amount INTEGER;
ALTER TABLE session_packages ADD COLUMN vat_amount INTEGER;
ALTER TABLE session_packages ADD COLUMN card_fee_amount INTEGER;
ALTER TABLE session_packages ADD COLUMN net_amount INTEGER;
ALTER TABLE session_packages ADD COLUMN vat_rate DECIMAL(5,2) DEFAULT 0.10;
ALTER TABLE session_packages ADD COLUMN card_fee_rate DECIMAL(5,2) DEFAULT 0.035;
ALTER TABLE session_packages ADD COLUMN fee_calculation_method VARCHAR(20) DEFAULT 'inclusive';
```

**New Fields Explanation:**
- `gross_amount`: Original charged amount (현재 total_amount과 동일)
- `vat_amount`: Calculated VAT amount
- `card_fee_amount`: Calculated card processing fee
- `net_amount`: Amount after deducting VAT and fees
- `vat_rate`: VAT rate (fixed at 10%)
- `card_fee_rate`: Card fee rate (fixed at 3.5%)
- `fee_calculation_method`: 'inclusive' or 'exclusive' for future flexibility

### 2. Enhanced payments Table

```sql
ALTER TABLE payments ADD COLUMN gross_amount INTEGER;
ALTER TABLE payments ADD COLUMN vat_amount INTEGER;
ALTER TABLE payments ADD COLUMN card_fee_amount INTEGER;
ALTER TABLE payments ADD COLUMN net_amount INTEGER;
ALTER TABLE payments ADD COLUMN vat_rate DECIMAL(5,2);
ALTER TABLE payments ADD COLUMN card_fee_rate DECIMAL(5,2);
```

### 3. New fee_audit_log Table

```sql
CREATE TABLE fee_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER,
    payment_id INTEGER,
    calculation_type VARCHAR(20), -- 'package_creation', 'credit_addition', 'fee_adjustment'
    gross_amount INTEGER NOT NULL,
    vat_amount INTEGER NOT NULL,
    card_fee_amount INTEGER NOT NULL,
    net_amount INTEGER NOT NULL,
    vat_rate DECIMAL(5,2) NOT NULL,
    card_fee_rate DECIMAL(5,2) NOT NULL,
    calculation_details TEXT, -- JSON with detailed calculation steps
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (package_id) REFERENCES session_packages(id),
    FOREIGN KEY (payment_id) REFERENCES payments(id),
    FOREIGN KEY (created_by) REFERENCES trainers(id)
);
```

## Payment Processing Flow

### 1. Package Creation Flow

```python
def create_package_with_fees(self, client_id: int, trainer_id: int, 
                           gross_amount: int, session_price: int,
                           package_name: str = None) -> SessionPackage:
    """
    Create a new package with VAT and fee calculations
    
    Args:
        gross_amount: Total amount charged to client (including all fees)
        session_price: Price per session (after fees)
    """
    # Step 1: Calculate fees
    fee_breakdown = self.calculate_fee_breakdown(gross_amount)
    
    # Step 2: Create package
    package = SessionPackage(
        client_id=client_id,
        trainer_id=trainer_id,
        package_name=package_name,
        gross_amount=gross_amount,
        vat_amount=fee_breakdown['vat_amount'],
        card_fee_amount=fee_breakdown['card_fee_amount'],
        net_amount=fee_breakdown['net_amount'],
        total_amount=gross_amount,  # Keep for backward compatibility
        session_price=session_price,
        total_sessions=fee_breakdown['net_amount'] // session_price,
        remaining_sessions=fee_breakdown['net_amount'] // session_price,
        remaining_credits=fee_breakdown['net_amount'],
        vat_rate=fee_breakdown['vat_rate'],
        card_fee_rate=fee_breakdown['card_fee_rate']
    )
    
    # Step 3: Create payment record
    payment = Payment(
        client_id=client_id,
        trainer_id=trainer_id,
        package_id=package.id,
        gross_amount=gross_amount,
        vat_amount=fee_breakdown['vat_amount'],
        card_fee_amount=fee_breakdown['card_fee_amount'],
        net_amount=fee_breakdown['net_amount'],
        amount=gross_amount,  # Keep for backward compatibility
        payment_method='card',
        description=f'패키지 구매: {package_name or "기본 패키지"}'
    )
    
    # Step 4: Create audit log
    self.create_fee_audit_log(
        package_id=package.id,
        payment_id=payment.id,
        calculation_type='package_creation',
        fee_breakdown=fee_breakdown
    )
    
    return package
```

### 2. Credit Addition Flow

```python
def add_credits_with_fees(self, package_id: int, gross_amount: int) -> bool:
    """Add credits to existing package with fee calculations"""
    package = self.get_package(package_id)
    if not package:
        return False
    
    # Calculate fees for additional amount
    fee_breakdown = self.calculate_fee_breakdown(gross_amount)
    
    # Update package
    additional_sessions = fee_breakdown['net_amount'] // package.session_price
    package.gross_amount += gross_amount
    package.vat_amount += fee_breakdown['vat_amount']
    package.card_fee_amount += fee_breakdown['card_fee_amount']
    package.net_amount += fee_breakdown['net_amount']
    package.total_sessions += additional_sessions
    package.remaining_sessions += additional_sessions
    package.remaining_credits += fee_breakdown['net_amount']
    
    # Create payment and audit records
    # ... (similar to package creation)
    
    return True
```

## VAT/Fee Calculation Logic

### Core Calculation Module

```python
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Union

class FeeCalculator:
    """Handles all fee calculations with fixed Korean tax rates"""
    
    def __init__(self):
        self.vat_rate = Decimal('0.10')  # Fixed 10% VAT
        self.card_fee_rate = Decimal('0.035')  # Fixed 3.5% card fee
    
    def calculate_fee_breakdown(self, gross_amount: Union[int, Decimal]) -> Dict:
        """
        Calculate VAT and card fees from gross amount
        
        Formula (inclusive method):
        - VAT Amount = Gross Amount × (VAT Rate ÷ (1 + VAT Rate))
        - Card Fee = Gross Amount × Card Fee Rate
        - Net Amount = Gross Amount - VAT Amount - Card Fee
        
        Returns:
            Dictionary with all calculated amounts as integers (KRW)
        """
        gross = Decimal(str(gross_amount))
        
        # Calculate VAT (부가세)
        vat_amount = gross * (self.vat_rate / (Decimal('1') + self.vat_rate))
        vat_amount = vat_amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        # Calculate card fee (카드 수수료)
        card_fee = gross * self.card_fee_rate
        card_fee = card_fee.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        # Calculate net amount
        net_amount = gross - vat_amount - card_fee
        
        return {
            'gross_amount': int(gross),
            'vat_amount': int(vat_amount),
            'card_fee_amount': int(card_fee),
            'net_amount': int(net_amount),
            'vat_rate': float(self.vat_rate),
            'card_fee_rate': float(self.card_fee_rate),
            'calculation_details': {
                'method': 'inclusive',
                'vat_formula': f'{gross} × ({self.vat_rate} ÷ (1 + {self.vat_rate}))',
                'fee_formula': f'{gross} × {self.card_fee_rate}',
                'precision': 'ROUND_HALF_UP'
            }
        }
    
    def validate_calculation(self, fee_breakdown: Dict) -> bool:
        """Validate that calculations are correct"""
        total = (fee_breakdown['net_amount'] + 
                fee_breakdown['vat_amount'] + 
                fee_breakdown['card_fee_amount'])
        return total == fee_breakdown['gross_amount']
```

### Integration with SessionManagementService

```python
class EnhancedSessionManagementService(SessionManagementService):
    def __init__(self, db: Database):
        super().__init__(db)
        self.fee_calculator = FeeCalculator()
    
    def calculate_fee_breakdown(self, gross_amount: int) -> Dict:
        """Calculate fees with validation"""
        breakdown = self.fee_calculator.calculate_fee_breakdown(gross_amount)
        
        if not self.fee_calculator.validate_calculation(breakdown):
            raise ValueError("Fee calculation validation failed")
        
        return breakdown
    
    def get_package_summary(self, package_id: int) -> Dict:
        """Get comprehensive package summary with fee breakdown"""
        package = self.get_package(package_id)
        if not package:
            return None
        
        # Calculate used amounts
        used_credits = package.net_amount - package.remaining_credits
        used_sessions = package.total_sessions - package.remaining_sessions
        
        return {
            'package_info': {
                'id': package.id,
                'name': package.package_name,
                'created_at': package.created_at
            },
            'financial_summary': {
                'gross_amount': package.gross_amount,
                'vat_amount': package.vat_amount,
                'card_fee_amount': package.card_fee_amount,
                'net_amount': package.net_amount,
                'vat_rate': package.vat_rate,
                'card_fee_rate': package.card_fee_rate
            },
            'usage_summary': {
                'total_sessions': package.total_sessions,
                'used_sessions': used_sessions,
                'remaining_sessions': package.remaining_sessions,
                'used_credits': used_credits,
                'remaining_credits': package.remaining_credits,
                'utilization_rate': (used_sessions / package.total_sessions * 100) 
                                   if package.total_sessions > 0 else 0
            }
        }
```

## UI Display Updates

### 1. Package Management Tab Enhancement

```python
def display_package_details(package: SessionPackage):
    """Enhanced package display with fee breakdown"""
    
    # Header section
    st.subheader(f"📦 {package.package_name or '기본 패키지'}")
    
    # Financial breakdown in expandable section
    with st.expander("💰 요금 상세 내역", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 충전 내역")
            st.metric("총 충전액", f"₩{package.gross_amount:,}")
            st.caption(f"부가세 (10%): ₩{package.vat_amount:,}")
            st.caption(f"카드 수수료 (3.5%): ₩{package.card_fee_amount:,}")
            st.metric("순 잔여 크래딧", f"₩{package.net_amount:,}")
        
        with col2:
            st.markdown("### 사용 현황")
            used_credits = package.net_amount - package.remaining_credits
            st.metric("사용 크래딧", f"₩{used_credits:,}")
            st.metric("남은 크래딧", f"₩{package.remaining_credits:,}")
            
            # Progress bar
            utilization = (used_credits / package.net_amount * 100) if package.net_amount > 0 else 0
            st.progress(utilization / 100)
            st.caption(f"이용률: {utilization:.1f}%")
    
    # Session details
    with st.expander("🏃 세션 정보"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 세션", f"{package.total_sessions}회")
        with col2:
            st.metric("사용 세션", f"{package.total_sessions - package.remaining_sessions}회")
        with col3:
            st.metric("남은 세션", f"{package.remaining_sessions}회")
```

### 2. Package Creation Form Enhancement

```python
def create_package_form():
    """Enhanced package creation with real-time fee calculation"""
    
    st.subheader("새 패키지 등록")
    
    with st.form("create_package"):
        col1, col2 = st.columns(2)
        
        with col1:
            gross_amount = st.number_input(
                "총 충전액 (VAT, 수수료 포함)",
                min_value=0,
                step=10000,
                help="고객이 실제로 결제하는 금액"
            )
            
            session_price = st.number_input(
                "세션당 가격",
                min_value=0,
                step=10000
            )
        
        with col2:
            # Real-time fee calculation display
            if gross_amount > 0:
                calculator = FeeCalculator()
                breakdown = calculator.calculate_fee_breakdown(gross_amount)
                
                st.info("**요금 계산 내역**")
                st.caption(f"총 충전액: ₩{breakdown['gross_amount']:,}")
                st.caption(f"부가세 (10%): ₩{breakdown['vat_amount']:,}")
                st.caption(f"카드 수수료 (3.5%): ₩{breakdown['card_fee_amount']:,}")
                st.success(f"**순 크래딧: ₩{breakdown['net_amount']:,}**")
                
                if session_price > 0:
                    total_sessions = breakdown['net_amount'] // session_price
                    st.info(f"**제공 가능 세션: {total_sessions}회**")
        
        package_name = st.text_input("패키지명 (선택사항)")
        notes = st.text_area("메모")
        
        submitted = st.form_submit_button("패키지 생성")
        
        if submitted and gross_amount > 0 and session_price > 0:
            # Create package with fee calculations
            service = EnhancedSessionManagementService(st.session_state.db)
            package = service.create_package_with_fees(
                client_id=client_id,
                trainer_id=trainer_id,
                gross_amount=gross_amount,
                session_price=session_price,
                package_name=package_name
            )
            st.success("패키지가 생성되었습니다!")
```

### 3. Payment History Enhancement

```python
def display_payment_history(payments: List[Payment]):
    """Enhanced payment history with fee breakdown"""
    
    for payment in payments:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.write(f"**{payment.payment_date.strftime('%Y-%m-%d')}**")
                st.caption(payment.description)
            
            with col2:
                st.write(f"총액: ₩{payment.gross_amount:,}")
                st.caption(f"VAT: ₩{payment.vat_amount:,} | 수수료: ₩{payment.card_fee_amount:,}")
            
            with col3:
                st.write(f"**순액: ₩{payment.net_amount:,}**")
            
            with col4:
                if st.button("상세", key=f"payment_{payment.id}"):
                    show_payment_details(payment)
```

## Migration Strategy

### 1. Database Migration Script

```python
"""
Alembic migration for adding VAT and fee support
"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal

def upgrade():
    # Add columns to session_packages
    op.add_column('session_packages', 
        sa.Column('gross_amount', sa.Integer(), nullable=True))
    op.add_column('session_packages', 
        sa.Column('vat_amount', sa.Integer(), nullable=True))
    op.add_column('session_packages', 
        sa.Column('card_fee_amount', sa.Integer(), nullable=True))
    op.add_column('session_packages', 
        sa.Column('net_amount', sa.Integer(), nullable=True))
    op.add_column('session_packages', 
        sa.Column('vat_rate', sa.Numeric(5, 2), nullable=True, default=0.10))
    op.add_column('session_packages', 
        sa.Column('card_fee_rate', sa.Numeric(5, 2), nullable=True, default=0.035))
    
    # Add columns to payments
    op.add_column('payments', 
        sa.Column('gross_amount', sa.Integer(), nullable=True))
    # ... (similar for other payment columns)
    
    # Create fee_audit_log table
    op.create_table('fee_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        # ... (other columns)
    )
    
    # Migrate existing data
    migrate_existing_packages()
    migrate_existing_payments()

def migrate_existing_packages():
    """
    Migrate existing packages assuming total_amount was gross amount
    """
    connection = op.get_bind()
    
    # Fetch all existing packages
    result = connection.execute(
        "SELECT id, total_amount FROM session_packages WHERE gross_amount IS NULL"
    )
    
    calculator = FeeCalculator()
    
    for row in result:
        package_id, total_amount = row
        
        # Calculate fee breakdown
        breakdown = calculator.calculate_fee_breakdown(total_amount)
        
        # Update package with calculated values
        connection.execute(
            f"""UPDATE session_packages 
            SET gross_amount = {breakdown['gross_amount']},
                vat_amount = {breakdown['vat_amount']},
                card_fee_amount = {breakdown['card_fee_amount']},
                net_amount = {breakdown['net_amount']},
                vat_rate = {breakdown['vat_rate']},
                card_fee_rate = {breakdown['card_fee_rate']}
            WHERE id = {package_id}"""
        )
        
        # Recalculate sessions based on net amount
        connection.execute(
            f"""UPDATE session_packages 
            SET total_sessions = net_amount / session_price,
                remaining_sessions = 
                    CASE 
                        WHEN remaining_sessions = total_sessions 
                        THEN net_amount / session_price
                        ELSE remaining_sessions * (net_amount / total_amount)
                    END,
                remaining_credits = remaining_credits * (net_amount / total_amount)
            WHERE id = {package_id}"""
        )

def downgrade():
    # Remove columns and tables
    op.drop_table('fee_audit_log')
    op.drop_column('session_packages', 'gross_amount')
    # ... (other rollback operations)
```

### 2. Data Validation Script

```python
def validate_migration():
    """Validate migrated data integrity"""
    
    validations = []
    
    # Check all packages have fee calculations
    packages_without_fees = db.query(
        "SELECT COUNT(*) FROM session_packages WHERE gross_amount IS NULL"
    )[0][0]
    validations.append({
        'check': 'Packages without fees',
        'result': packages_without_fees == 0,
        'count': packages_without_fees
    })
    
    # Validate calculation accuracy
    invalid_calculations = db.query("""
        SELECT COUNT(*) FROM session_packages 
        WHERE gross_amount != (net_amount + vat_amount + card_fee_amount)
    """)[0][0]
    validations.append({
        'check': 'Invalid calculations',
        'result': invalid_calculations == 0,
        'count': invalid_calculations
    })
    
    # Check session count consistency
    session_mismatches = db.query("""
        SELECT COUNT(*) FROM session_packages 
        WHERE total_sessions != (net_amount / session_price)
    """)[0][0]
    validations.append({
        'check': 'Session count mismatches',
        'result': session_mismatches == 0,
        'count': session_mismatches
    })
    
    return validations
```

## Technical Considerations

### 1. Decimal Precision Handling

```python
class MoneyField:
    """Custom field for handling monetary values with proper precision"""
    
    @staticmethod
    def to_decimal(value: Union[int, float, Decimal]) -> Decimal:
        """Convert to Decimal with proper precision"""
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    
    @staticmethod
    def to_int_krw(value: Decimal) -> int:
        """Convert to integer KRW with proper rounding"""
        return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
```

### 2. Financial Transaction Auditing

```python
class AuditLogger:
    """Comprehensive audit logging for financial transactions"""
    
    def log_fee_calculation(self, package_id: int, payment_id: int, 
                          calculation_type: str, fee_breakdown: Dict):
        """Log fee calculation details"""
        audit_entry = FeeAuditLog(
            package_id=package_id,
            payment_id=payment_id,
            calculation_type=calculation_type,
            gross_amount=fee_breakdown['gross_amount'],
            vat_amount=fee_breakdown['vat_amount'],
            card_fee_amount=fee_breakdown['card_fee_amount'],
            net_amount=fee_breakdown['net_amount'],
            vat_rate=fee_breakdown['vat_rate'],
            card_fee_rate=fee_breakdown['card_fee_rate'],
            calculation_details=json.dumps(fee_breakdown['calculation_details']),
            created_by=current_user_id()
        )
        db.save(audit_entry)
```

### 3. Localization Support

```python
class CurrencyFormatter:
    """Handle Korean Won currency formatting"""
    
    @staticmethod
    def format(amount: int) -> str:
        """Format amount as Korean Won"""
        return f"₩{amount:,}"
    
    @staticmethod
    def format_short(amount: int) -> str:
        """Format large amounts in shortened form"""
        if amount >= 10000:
            return f"₩{amount // 10000:,}만원"
        return f"₩{amount:,}"
```

### 4. Error Handling

```python
class FeeCalculationError(Exception):
    """Custom exception for fee calculation errors"""
    pass

def safe_fee_calculation(gross_amount: int) -> Dict:
    """Calculate fees with comprehensive error handling"""
    try:
        if gross_amount <= 0:
            raise FeeCalculationError("Amount must be positive")
        
        if gross_amount > 999999999:  # 1 billion KRW
            raise FeeCalculationError("Amount exceeds maximum limit")
        
        calculator = FeeCalculator()
        breakdown = calculator.calculate_fee_breakdown(gross_amount)
        
        if not calculator.validate_calculation(breakdown):
            raise FeeCalculationError("Calculation validation failed")
        
        return breakdown
        
    except Decimal.InvalidOperation as e:
        raise FeeCalculationError(f"Invalid decimal operation: {e}")
    except Exception as e:
        logger.error(f"Fee calculation error: {e}")
        raise FeeCalculationError(f"Calculation failed: {e}")
```

## Testing Scenarios

### 1. Unit Tests

```python
class TestFeeCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = FeeCalculator()
    
    def test_standard_calculation(self):
        """Test standard fee calculation"""
        result = self.calculator.calculate_fee_breakdown(1980000)
        
        self.assertEqual(result['gross_amount'], 1980000)
        self.assertEqual(result['vat_amount'], 180000)  # 10% VAT
        self.assertEqual(result['card_fee_amount'], 69300)  # 3.5% fee
        self.assertEqual(result['net_amount'], 1730700)
    
    def test_boundary_values(self):
        """Test minimum and maximum values"""
        # Minimum value
        min_result = self.calculator.calculate_fee_breakdown(1)
        self.assertEqual(min_result['gross_amount'], 1)
        
        # Maximum value
        max_result = self.calculator.calculate_fee_breakdown(999999999)
        self.assertTrue(max_result['net_amount'] > 0)
    
    def test_rounding_edge_cases(self):
        """Test rounding behavior"""
        # Test case that results in fractional amounts
        result = self.calculator.calculate_fee_breakdown(12345)
        
        # Verify total equals gross
        total = (result['net_amount'] + 
                result['vat_amount'] + 
                result['card_fee_amount'])
        self.assertEqual(total, result['gross_amount'])
```

### 2. Integration Tests

```python
class TestPackageCreation(unittest.TestCase):
    def test_create_package_with_fees(self):
        """Test complete package creation flow"""
        service = EnhancedSessionManagementService(test_db)
        
        package = service.create_package_with_fees(
            client_id=1,
            trainer_id=1,
            gross_amount=1980000,
            session_price=60000,
            package_name="테스트 패키지"
        )
        
        # Verify package created correctly
        self.assertEqual(package.gross_amount, 1980000)
        self.assertEqual(package.net_amount, 1730700)
        self.assertEqual(package.total_sessions, 28)  # 1730700 / 60000
        
        # Verify payment record created
        payment = test_db.get_latest_payment(package.id)
        self.assertEqual(payment.gross_amount, 1980000)
        
        # Verify audit log created
        audit = test_db.get_latest_audit_log(package.id)
        self.assertIsNotNone(audit)
```

### 3. Migration Tests

```python
class TestDataMigration(unittest.TestCase):
    def test_existing_package_migration(self):
        """Test migration of existing packages"""
        # Create old-style package
        old_package = create_legacy_package(
            total_amount=1980000,
            session_price=60000
        )
        
        # Run migration
        migrate_existing_packages()
        
        # Verify migrated data
        migrated = get_package(old_package.id)
        self.assertEqual(migrated.gross_amount, 1980000)
        self.assertEqual(migrated.net_amount, 1730700)
        self.assertEqual(migrated.vat_amount, 180000)
```

### 4. Concurrent Transaction Tests

```python
class TestConcurrentOperations(unittest.TestCase):
    def test_concurrent_credit_additions(self):
        """Test concurrent credit additions"""
        package_id = create_test_package().id
        
        # Simulate concurrent additions
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for _ in range(5):
                future = executor.submit(
                    add_credits_with_fees, 
                    package_id, 
                    100000
                )
                futures.append(future)
            
            # Wait for all to complete
            results = [f.result() for f in futures]
        
        # Verify final state is consistent
        final_package = get_package(package_id)
        expected_gross = initial_gross + (100000 * 5)
        self.assertEqual(final_package.gross_amount, expected_gross)
```

## Implementation Timeline

### Phase 1: Database and Core Logic (Week 1)
- Day 1-2: Create database migration scripts
- Day 3-4: Implement FeeCalculator and validation
- Day 5: Migrate existing data and validate

### Phase 2: Service Layer Integration (Week 2)
- Day 1-2: Update SessionManagementService
- Day 3-4: Implement audit logging
- Day 5: Integration testing

### Phase 3: UI Updates (Week 3)
- Day 1-2: Update package management UI
- Day 3-4: Update payment history display
- Day 5: User acceptance testing

### Phase 4: Testing and Deployment (Week 4)
- Day 1-2: Comprehensive testing
- Day 3: Performance optimization
- Day 4: Production deployment preparation
- Day 5: Production deployment and monitoring

## Rollback Strategy

### Database Rollback

```sql
-- Rollback script for emergency use
BEGIN TRANSACTION;

-- Restore original values
UPDATE session_packages 
SET total_amount = gross_amount,
    remaining_credits = remaining_credits * (gross_amount / net_amount)
WHERE gross_amount IS NOT NULL;

-- Remove new columns
ALTER TABLE session_packages DROP COLUMN gross_amount;
ALTER TABLE session_packages DROP COLUMN vat_amount;
-- ... (other columns)

DROP TABLE fee_audit_log;

COMMIT;
```

### Application Rollback

1. Deploy previous version of application
2. Run database rollback script
3. Clear caches
4. Verify system functionality

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Calculation Accuracy**
   - Monitor for calculation mismatches
   - Alert if gross != net + vat + fee

2. **Migration Progress**
   - Track packages migrated
   - Monitor for migration errors

3. **Performance Impact**
   - Query execution times
   - UI response times

4. **User Experience**
   - Error rates
   - Support ticket volume

## Conclusion

This implementation plan provides a comprehensive approach to adding VAT and card processing fee calculations to the fitness assessment system. The solution maintains backward compatibility while providing transparent fee breakdowns and robust audit trails. The phased implementation approach minimizes risk and allows for thorough testing at each stage.