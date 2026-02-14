export enum StaffRole {
  owner = "owner",
  staff = "staff",
}

export interface StaffCreate {
  email: string;
  full_name?: string;
  role?: StaffRole;
  is_active?: boolean;
}

export interface StaffUpdate {
  full_name?: string;
  role?: StaffRole;
  is_active?: boolean;
}

export interface StaffOut {
  id: string;
  email: string;
  full_name?: string;
  role: StaffRole;
  is_active: boolean;
  created_at: string;
}
