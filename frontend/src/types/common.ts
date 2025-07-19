/**
 * Common utility types used throughout the application
 */

// Generic utility types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type Nullable<T> = T | null;
export type Maybe<T> = T | null | undefined;

// Function types
export type AsyncFunction<T = void> = () => Promise<T>;
export type AsyncFunctionWithArgs<TArgs extends any[], TReturn = void> = (...args: TArgs) => Promise<TReturn>;
export type EventHandler<T = any> = (event: T) => void;
export type AsyncEventHandler<T = any> = (event: T) => Promise<void>;

// State management types
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
  lastUpdated?: Date;
}

export interface AsyncState<T> extends LoadingState {
  data: T | null;
}

export interface PaginatedState<T> extends AsyncState<T[]> {
  page: number;
  pageSize: number;
  totalCount: number;
  hasMore: boolean;
}

// API-related types
export interface ApiRequestConfig {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
  timestamp?: Date;
}

// Validation types
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export type Validator<T> = (value: T) => ValidationResult;

// Configuration types
export interface AppConfig {
  apiBaseUrl: string;
  apiTimeout: number;
  mapCenter: [number, number];
  mapZoom: number;
  enableDebugMode: boolean;
  maxRetries: number;
  retryDelay: number;
}

export interface EnvironmentConfig {
  development: AppConfig;
  production: AppConfig;
  test: AppConfig;
}

// Event types
export interface CustomEvent<T = any> {
  type: string;
  data: T;
  timestamp: Date;
  source?: string;
}

export type EventListener<T = any> = (event: CustomEvent<T>) => void;

// Storage types
export interface StorageItem<T = any> {
  key: string;
  value: T;
  timestamp: Date;
  expiresAt?: Date;
}

export type StorageType = 'localStorage' | 'sessionStorage' | 'memory';

// Theme and styling types
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      bold: number;
    };
  };
  breakpoints: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// Date and time types
export type DateString = string; // ISO 8601 format
export type TimeString = string; // HH:MM:SS format
export type DateTimeString = string; // ISO 8601 format with time

export interface DateRange {
  start: Date;
  end: Date;
}

export interface TimeRange {
  start: TimeString;
  end: TimeString;
}

// File and media types
export interface FileInfo {
  name: string;
  size: number;
  type: string;
  lastModified: Date;
  path?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// Search and filter types
export interface SearchOptions {
  query: string;
  fields?: string[];
  caseSensitive?: boolean;
  exactMatch?: boolean;
  limit?: number;
  offset?: number;
}

export interface FilterOptions<T = any> {
  field: keyof T;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'contains' | 'startsWith' | 'endsWith';
  value: any;
}

export interface SortOptions<T = any> {
  field: keyof T;
  direction: 'asc' | 'desc';
}

// Permission and security types
export interface Permission {
  resource: string;
  action: string;
  granted: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  permissions: Permission[];
  lastLogin?: Date;
  isActive: boolean;
}

// Logging types
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: Date;
  source?: string;
  data?: any;
}

// Performance monitoring types
export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: Date;
  tags?: Record<string, string>;
}

// Generic collection types
export type Collection<T> = T[];
export type Dictionary<T> = Record<string, T>;
export type KeyValuePair<K = string, V = any> = { key: K; value: V };

// Utility type for creating branded types
export type Brand<T, B> = T & { __brand: B };

// ID types
export type ID = Brand<string, 'ID'>;
export type UUID = Brand<string, 'UUID'>;
export type NumericID = Brand<number, 'NumericID'>;

// Status types
export type Status = 'idle' | 'loading' | 'success' | 'error';
export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'reconnecting';

// Generic result types
export interface Result<T, E = Error> {
  success: boolean;
  data?: T;
  error?: E;
}

export type AsyncResult<T, E = Error> = Promise<Result<T, E>>;