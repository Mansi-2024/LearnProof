import AuthForm from "@/components/ui/AuthForm";

export const metadata = {
  title: "Log in — Repair",
};

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <AuthForm mode="login" />
    </main>
  );
}
