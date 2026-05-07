# Plan: DataQ Platform Enhancements

## Summary
Implement 4 key enhancements to the DataQ data quality platform.

## Deliverables
1. SQLite database connector support
2. Real 7-day validation trend data API + frontend integration
3. Table render protection for data preview
4. Rule edit functionality verification

## Effort: Medium
## Parallel: NO (sequential file updates)

## Context

### Original Request
User requested 4 changes:
1. Fix quality dashboard validation trend (currently fake data)
2. Fix rule edit functionality (not working)
3. Add SQLite database support
4. Add table render protection for data preview (prevent blank pages with many columns)

### Current State Analysis
- **db_connector.py**: Already has MySQL, PostgreSQL, SQLServer, Oracle connectors. Missing SQLite.
- **routes.py**: Has `/statistics/overview` but missing `/statistics/trend` endpoint.
- **dashboard.js**: Uses hardcoded fake data for trend chart.
- **asset_detail.js**: No render protection for data preview tables.
- **assets.html**: Missing SQLite datasource option in UI.

## Work Objectives

### Core Objective
Make DataQ more robust with real trend data, SQLite support, and safer table rendering.

### Definition of Done
1. ✅ SQLiteConnector class added and registered in factory
2. ✅ `/statistics/trend` API returns 7 days of validation data
3. ✅ Dashboard loads real trend data from API
4. ✅ Data preview includes `checkRenderHealth()` protection
5. ✅ SQLite option available in asset creation UI

### Must Have
- SQLite connector with full CRUD
- Trend API returning date-based stats
- Graceful fallback if trend API fails
- Render health check for preview tables

### Must NOT Have
- Breaking changes to existing database connectors
- No performance degradation in dashboard

## Verification Strategy
1. **Backend**: Test API endpoints with curl/Invoke-RestMethod
2. **Frontend**: Browser console verification of chart data
3. **Integration**: End-to-end test of SQLite data source creation
4. **Render protection**: Test with 20+ column CSV to verify protection triggers

## Execution Strategy

### Tasks (4 total)

---

#### Task 1: Add SQLite Database Connector

**File**: `src/backend/integrations/db_connector.py`

Add `SQLiteConnector` class before `create_connector` factory function:

```python
class SQLiteConnector(DatabaseConnector):
    """SQLite 数据库连接器"""
    
    def __init__(self, db_path: str, **kwargs):
        connection_string = f"sqlite:///{db_path}"
        if kwargs:
            params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
            connection_string += f"?{params}"
        super().__init__(connection_string)
        self.db_path = db_path
    
    def get_db_type(self) -> str:
        return "SQLite"
    
    def get_table_info(self, table_name: str) -> Dict:
        query = f"PRAGMA table_info('{table_name}')"
        df = self.execute_query(query)
        
        columns = []
        for _, row in df.iterrows():
            columns.append({
                'COLUMN_NAME': row['name'],
                'DATA_TYPE': row['type'],
                'IS_NULLABLE': 'NO' if row['notnull'] else 'YES',
                'COLUMN_DEFAULT': row['dflt_value'],
                'PRIMARY_KEY': bool(row['pk'])
            })
        
        count_query = f"SELECT COUNT(*) as cnt FROM '{table_name}'"
        count_df = self.execute_query(count_query)
        row_count = count_df.iloc[0]['cnt'] if len(count_df) > 0 else 0
        
        return {'table_name': table_name, 'columns': columns, 'row_count': row_count}
```

Update factory registration:
- Add `'sqlite': SQLiteConnector` to `connectors` dict
- Update docstring to include 'sqlite' in supported types

**Verification**: Python syntax check + import test

---

#### Task 2: Add Validation Trend API Endpoint

**File**: `src/backend/api/routes.py` (after line 1810)

Add new endpoint:

```python
@api_bp.route('/statistics/trend', methods=['GET'])
def get_validation_trend():
    """获取最近7天的校验趋势数据"""
    try:
        session = get_db_session()
        try:
            from datetime import datetime, timedelta
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
            trend_data = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                success_count = session.query(ValidationHistory).filter(
                    ValidationHistory.executed_at >= day_start,
                    ValidationHistory.executed_at <= day_end,
                    ValidationHistory.status == 'completed'
                ).count()
                
                failed_count = session.query(ValidationHistory).filter(
                    ValidationHistory.executed_at >= day_start,
                    ValidationHistory.executed_at <= day_end,
                    ValidationHistory.status != 'completed'
                ).count()
                
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_label': current_date.strftime('%a'),
                    'success': success_count,
                    'failed': failed_count
                })
                
                current_date += timedelta(days=1)
            
            return jsonify({
                'status': 'success',
                'data': {'trend': trend_data, 'days': 7}
            })
        finally:
            session.close()
    except Exception as e:
        return handle_error(e)
```

**Verification**: Test endpoint returns 7 days of data (may be zeros if no history)

---

#### Task 3: Update Dashboard to Use Real Trend Data

**File**: `src/frontend/static/js/dashboard.js`

Replace `drawValidationTrendChart()` function (lines 80-127) to:
1. Call `${API_BASE_URL}/statistics/trend` API
2. Map response data to chart labels and datasets
3. Add graceful fallback to zeros if API fails
4. Preserve existing chart styling (green for success, red for failed)

**Verification**: Browser network tab shows API call + chart renders with real data

---

#### Task 4: Add Table Render Protection to Data Preview

**File**: `src/frontend/static/js/asset_detail.js`

Add two functions after `renderDataPreview`:

1. `checkRenderHealth(container)` - Detects rendering anomalies
   - Checks for visible dimensions (>10x10px)
   - Verifies display != none and visibility != hidden
   - Checks opacity > 0.1 and in viewport
   - Shows warning alert with refresh button if anomaly detected

2. `forceShowFullTable(btn)` - Performance-protected full render
   - Confirmation dialog before proceeding
   - Disables button during rendering
   - Uses setTimeout to prevent UI blocking

Update `renderDataPreview` to call `checkRenderHealth(container)` at the end.

**Verification**: Test with 20+ column file to verify protection triggers

---

## Final Verification Wave (MANDATORY)

After ALL implementation tasks complete:

1. **F1. Backend API Test** - Test all new endpoints
2. **F2. Dashboard Render Test** - Verify chart loads real data
3. **F3. SQLite Connector Test** - Verify connection to test DB
4. **F4. Render Protection Test** - Verify with large CSV

## Commit Strategy

Single commit: `feat: add SQLite support, real trend data, and render protection`

## Success Criteria

- ✅ New SQLite connector passes import and instantiation
- ✅ Trend API returns 7 days of data in correct format
- ✅ Dashboard no longer uses hardcoded fake data
- ✅ Data preview has render health check protection
- ✅ All existing tests still pass
