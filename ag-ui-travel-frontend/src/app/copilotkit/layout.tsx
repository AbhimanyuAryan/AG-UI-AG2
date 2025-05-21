import "@copilotkit/react-ui/styles.css";
import React, { ReactNode } from "react";
import { CopilotKit } from "@copilotkit/react-core";

// Where CopilotKit will proxy requests to. If you're using Copilot Cloud, this environment variable will be empty.
const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL;

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <CopilotKit
      runtimeUrl={runtimeUrl}
      agent="travelAgent" // The name of the agent to use
    >
      {children}
    </CopilotKit>
  );
}
