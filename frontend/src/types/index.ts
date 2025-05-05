export interface Port {
  id: number | null
  host: string
  port_number: number | null
  proto: string
  status: string
  banner: string | null
  last_seen: string
  scan: number | null
}

export interface Domain {
  id: number
  host: string
  name: string
  source: string
}

export interface SSLCertificate {
  id: number
  fingerprint: string
  subject_cn: string | null
  issuer_cn: string | null
  valid_from: string
  valid_until: string
  created_at: string
  updated_at: string
  port: number
  host: number
}

export interface Host {
  id: number | null
  ports: Port[]
  domains: Domain[]
  ssl_certificates: SSLCertificate[]
  ip: string
  private: boolean | null
  last_seen: string | null
  public_host: boolean | null
  scan: number | null
  score: number | null
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  page: number
  page_size: number
  results: T[]
}

export type PaginatedHosts = PaginatedResponse<Host> 