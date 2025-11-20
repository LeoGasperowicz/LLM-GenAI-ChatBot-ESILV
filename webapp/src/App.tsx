import React, { useState } from "react";
import { Layout } from "./components/Layout";
import { ChatPage } from "./components/ChatPage";
import { AdminPage } from "./components/AdminPage";

export const App: React.FC = () => {
  const [page, setPage] = useState<"chat" | "admin">("chat");

  return (
    <Layout page={page} onChangePage={setPage}>
      {page === "chat" ? <ChatPage /> : <AdminPage />}
    </Layout>
  );
};
