export type AnalysisMode = "deep_report" | "quick_scan" | "theme_research";

export type ThreadSummary = {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
};

export type JobEvent = {
  id: string;
  event: string;
  message: string;
  created_at: string;
};

export type JobRecord = {
  id: string;
  thread_id: string;
  user_id: string;
  status: "queued" | "running" | "completed" | "failed" | "canceled";
  created_at: string;
  updated_at: string;
  request: {
    run_id: string;
    user_id: string;
    thread_id: string;
    analysis_mode: AnalysisMode;
    target_type: "ticker" | "theme" | "question";
    target_value: string;
    question: string;
    risk_profile: "conservative" | "balanced" | "aggressive";
    preferred_language: "zh-CN" | "en-US";
    selected_skill_profile: string;
  };
  result?: {
    run_id: string;
    status: "queued" | "running" | "completed" | "failed" | "canceled";
    report_summary?: {
      title: string;
      summary: string;
      rating: string;
      confidence: number;
    };
  } | null;
};

export type ReportRecord = {
  id: string;
  thread_id: string;
  job_id: string;
  user_id: string;
  title: string;
  target_value: string;
  analysis_mode: AnalysisMode;
  summary: string;
  rating: string;
  markdown: string;
  created_at: string;
};
