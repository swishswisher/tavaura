import { NextResponse } from "next/server";

type SignupPayload = {
  email?: string;
  from?: string;
};

const signupLeads: { email: string; from?: string; at: string }[] = [];

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as SignupPayload;
    const email = body?.email?.trim();
    const from = body?.from?.trim() || undefined;

    if (!email || !email.includes("@")) {
      return new NextResponse(JSON.stringify({ error: "Invalid email" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const record = { email, from, at: new Date().toISOString() };
    signupLeads.push(record);
    console.log("[Tavaura signup]", record);

    return new NextResponse(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    return new NextResponse(JSON.stringify({ error: "Invalid request" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
}
