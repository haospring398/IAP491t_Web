import Ajv from "ajv";
import schema from "../../contracts/analysis.schema.json";
import policySchema from "../../contracts/transport-policy.schema.json";
import policyData from "../../contracts/transport-policy.json";
import type { AnalysisSuccess, AnalysisError, AnalysisStatus, RequestId, TransportPolicy } from "./contracts.generated";
export type { AnalysisSuccess, AnalysisError, AnalysisStatus, RequestId } from "./contracts.generated";
export type ErrorCode = AnalysisError["error"]["code"];
const ajv = new Ajv({ strict: true, allErrors: false });
ajv.addSchema(schema);
export const isSuccess = ajv.compile<AnalysisSuccess>({ $ref: "urn:iap:analysis:v1#/definitions/AnalysisSuccess" });
export const isError = ajv.compile<AnalysisError>({ $ref: "urn:iap:analysis:v1#/definitions/AnalysisError" });
export const isStatus = ajv.compile<AnalysisStatus>({ $ref: "urn:iap:analysis:v1#/definitions/AnalysisStatus" });
export const isRequestId = ajv.compile<RequestId>({ $ref: "urn:iap:analysis:v1#/definitions/RequestId" });
export function validatePolicy(value: unknown): asserts value is TransportPolicy {
  if (!ajv.validate(policySchema, value)) throw new Error("Invalid shared transport policy");
  const p = value as TransportPolicy;
  const inputCodes: ErrorCode[] = ["INVALID_REQUEST", "EMAIL_TOO_LARGE", "EMPTY_EMAIL", "INVALID_EMAIL", "INSUFFICIENT_CONTENT", "RESOURCE_LIMIT"];
  for (const [code, error] of Object.entries(p.errors)) {
    if (inputCodes.includes(code as ErrorCode) ? error.retryAfterSeconds !== 0 : error.retryAfterSeconds === 0) {
      throw new Error("Inconsistent shared recovery policy");
    }
  }
  if (!(p.limits.fileBytes < p.limits.multipartBytes &&
    p.deadlines.backendMs < p.deadlines.proxyMs && p.deadlines.proxyMs < p.deadlines.browserMs &&
    p.deadlines.backendReserveMs >= p.deadlines.clockSkewMs + p.deadlines.terminateMs + p.deadlines.killReapMs)) {
    throw new Error("Inconsistent shared transport policy");
  }
}
validatePolicy(policyData);
export const policy: Readonly<TransportPolicy> = policyData;
export function errorEnvelope(code: ErrorCode, requestId: string): AnalysisError {
  return { error: { code, message: policy.errors[code].message }, request_id: requestId };
}
export function isCorrelated(header: string | null, requestId: string): boolean { return header === requestId; }
export function isJsonMediaType(value: string | null): boolean { return /^application\/json(?:\s*;|$)/i.test(value || ""); }
