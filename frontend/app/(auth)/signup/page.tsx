import AuthForm from "@/components/ui/AuthForm";

export const metadata = {
  title: "Sign up — Repair",
};

export default function SignupPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <AuthForm mode="signup" />
    </main>
  );
}
