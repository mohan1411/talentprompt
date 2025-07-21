# Resume Statistics API Endpoint

## Overview

The `/api/v1/resumes/statistics` endpoint provides resume upload statistics grouped by date, suitable for creating bar charts and other visualizations.

## Endpoint Details

- **URL**: `/api/v1/resumes/statistics`
- **Method**: `GET`
- **Authentication**: Required (Bearer token)

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| aggregation | string | No | daily | Grouping type: `daily`, `weekly`, `monthly`, or `yearly` |
| start_date | datetime | No | None | Filter start date (ISO format) |
| end_date | datetime | No | None | Filter end date (ISO format) |

## Response Format

```json
{
  "aggregation": "daily",
  "data": [
    {
      "date": "2025-07-15",
      "count": 5
    },
    {
      "date": "2025-07-16",
      "count": 8
    },
    {
      "date": "2025-07-17",
      "count": 3
    }
  ],
  "total_count": 16,
  "start_date": "2025-07-15",
  "end_date": "2025-07-17"
}
```

## Date Formats by Aggregation

- **daily**: `YYYY-MM-DD` (e.g., "2025-07-21")
- **weekly**: `YYYY-WXX` (e.g., "2025-W29")
- **monthly**: `YYYY-MM` (e.g., "2025-07")
- **yearly**: `YYYY` (e.g., "2025")

## Usage Examples

### Get daily statistics for the last 30 days

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/statistics?aggregation=daily&start_date=2025-06-21T00:00:00&end_date=2025-07-21T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get monthly statistics for the current year

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/statistics?aggregation=monthly&start_date=2025-01-01T00:00:00" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get weekly statistics without date filters

```bash
curl -X GET "http://localhost:8000/api/v1/resumes/statistics?aggregation=weekly" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Frontend Integration

This endpoint is designed to work seamlessly with chart libraries like Chart.js, D3.js, or Recharts:

```javascript
// Example with Chart.js
const response = await fetch('/api/v1/resumes/statistics?aggregation=daily', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const data = await response.json();

const chartData = {
  labels: data.data.map(item => item.date),
  datasets: [{
    label: 'Resume Uploads',
    data: data.data.map(item => item.count),
    backgroundColor: 'rgba(54, 162, 235, 0.5)',
    borderColor: 'rgba(54, 162, 235, 1)',
    borderWidth: 1
  }]
};
```

## Permissions

- **Regular users**: See statistics only for their own resume uploads
- **Admin users**: See statistics for all resume uploads in the system

## Error Responses

- **401 Unauthorized**: Missing or invalid authentication token
- **422 Unprocessable Entity**: Invalid query parameters (e.g., invalid aggregation type)
- **500 Internal Server Error**: Database or server error