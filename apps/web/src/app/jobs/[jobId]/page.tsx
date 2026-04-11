"use client";

import { useEffect, useState } from "react";

import { getJobResult } from "../../../lib/api-client";
import { GetJobResultResponse } from "../../../lib/types";

export default function JobPage({ params }: { params: { jobId: string } }) {
  const [data, setData] = useState<GetJobResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJobResult(params.jobId)
      .then(setData)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "Failed to load job"));
  }, [params.jobId]);

  return (
    <main style={{ padding: 24 }}>
      <h1>Job {params.jobId}</h1>
      {error ? <p>{error}</p> : null}
      {!data ? <p>Loading...</p> : (
        <>
          <p>Status: {data.status}</p>
          <p>Images: {data.result?.images.length ?? 0}</p>
          <p>Warnings: {data.result?.warnings.join(", ") || "none"}</p>
        </>
      )}
    </main>
  );
}
