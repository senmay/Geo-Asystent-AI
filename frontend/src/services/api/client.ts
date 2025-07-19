/**
 * HTTP client with retry logic, timeout handling, and error management
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { defaultApiConfig } from './config';
import type { ApiConfig, ApiError, ApiResponse, RequestOptions } from './types';

export class ApiClient {
  private client: AxiosInstance;
  private config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = { ...defaultApiConfig, ...config };
    this.client = this.createAxiosInstance();
    this.setupInterceptors();
  }

  private createAxiosInstance(): AxiosInstance {
    return axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ Response Error:', error.response?.status, error.response?.data);
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: any): ApiError {
    if (error.response) {
      // Server responded with error status
      return {
        message: error.response.data?.detail || error.response.data?.message || 'Server error',
        status: error.response.status,
        code: error.response.data?.code,
        details: error.response.data,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        message: 'Network error - no response from server',
        code: 'NETWORK_ERROR',
      };
    } else {
      // Something else happened
      return {
        message: error.message || 'Unknown error occurred',
        code: 'UNKNOWN_ERROR',
      };
    }
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async executeWithRetry<T>(
    operation: () => Promise<AxiosResponse<T>>,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const maxRetries = options.retries ?? this.config.retryAttempts;
    let lastError: ApiError;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await operation();
        return {
          data: response.data,
          status: response.status,
          statusText: response.statusText,
        };
      } catch (error) {
        lastError = error as ApiError;
        
        // Don't retry on client errors (4xx) or if it's the last attempt
        if (lastError.status && lastError.status < 500 || attempt === maxRetries) {
          throw lastError;
        }

        // Wait before retrying
        if (attempt < maxRetries) {
          const delay = this.config.retryDelay * Math.pow(2, attempt); // Exponential backoff
          console.log(`⏳ Retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
          await this.sleep(delay);
        }
      }
    }

    throw lastError!;
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.executeWithRetry(
      () => this.client.get<T>(url, { ...config, signal: options?.signal }),
      options
    );
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.executeWithRetry(
      () => this.client.post<T>(url, data, { ...config, signal: options?.signal }),
      options
    );
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.executeWithRetry(
      () => this.client.put<T>(url, data, { ...config, signal: options?.signal }),
      options
    );
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.executeWithRetry(
      () => this.client.delete<T>(url, { ...config, signal: options?.signal }),
      options
    );
  }

  // Update configuration
  updateConfig(newConfig: Partial<ApiConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.client.defaults.baseURL = this.config.baseURL;
    this.client.defaults.timeout = this.config.timeout;
  }

  // Get current configuration
  getConfig(): ApiConfig {
    return { ...this.config };
  }
}