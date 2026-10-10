import { analyzeProxy } from "@/lib/proxy";
import { backendConfig } from "@/lib/server-config";
export const runtime = "nodejs";
// Static route value required by Next; asserted against the shared policy in tests.
export const maxDuration = 180;
export async function POST(request: Request) { return analyzeProxy(request, backendConfig()); }
