// Frontend Configuration Constants
// This file centralizes all hardcoded values to make them configurable

export const JOB_SOURCES = {
  LINKEDIN: {
    name: 'LinkedIn',
    url: 'https://www.linkedin.com/jobs',
    description: 'Professional networking platform with global job opportunities'
  },
  TOPCV: {
    name: 'TopCV',
    url: 'https://www.topcv.vn',
    description: 'Leading Vietnamese job portal for all industries'
  },
  ITVIEC: {
    name: 'ITViec',
    url: 'https://www.itviec.com',
    description: 'Specialized IT job platform for Vietnam market'
  },
  VIETNAMWORKS: {
    name: 'VietnamWorks',
    url: 'https://www.vietnamworks.com',
    description: 'Comprehensive job portal covering all Vietnamese industries'
  },
  OTHER: {
    name: 'Other',
    url: '#',
    description: 'Other job source platforms'
  }
} as const;

export const SOURCE_CONFIGURATION = {
  DEFAULT_CRAWL_SCHEDULE: 'Every 6 hours during business hours (9 AM - 6 PM)',
  DATA_RETENTION_DAYS: 90,
  DATA_RETENTION_DESCRIPTION: 'Job data is retained for 90 days by default. Expired jobs are automatically removed to maintain optimal search performance.'
} as const;

export const MOCK_DATES = {
  // Using current date for development
  DEFAULT_LAST_CRAWL: new Date(),
  LINKEDIN_LAST_CRAWL: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
  TOPCV_LAST_CRAWL: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
  ITVIEC_LAST_CRAWL: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
  VIETNAMWORKS_LAST_CRAWL: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000) // 5 days ago
} as const;

export const UI_MESSAGES = {
  ADD_SOURCE: {
    title: 'Add Source functionality',
    content: `Available source types:
- LinkedIn
- TopCV
- ITViec
- VietnamWorks
- Other

This would typically open a configuration form to add a new data source.`
  },
  SETTINGS: {
    configurationOptions: [
      'Enable/Disable source',
      'Set crawl frequency',
      'Configure crawl parameters',
      'View crawl logs'
    ]
  }
} as const;

export const DATE_FORMATS = {
  LOCAL_DATE: 'toLocaleDateString',
  LOCAL_STRING: 'toLocaleString',
  ISO_STRING: 'toISOString'
} as const;
