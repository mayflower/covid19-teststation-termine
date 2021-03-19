import React, { useState } from "react";
import FocusLock from "react-focus-lock";
import { AddUser } from "./AddUser";
import { UserTable } from "./UserTable";

export const UserManagement = () => {
  const [triggerRefresh, setTriggerRefresh] = useState(true);
  const refreshList = () => setTriggerRefresh(true);

  return (
    <div className="container">
      <header>
        <h3 style={{ paddingLeft: "var(--universal-padding)" }}>
          {window.config.longInstanceName}
        </h3>
      </header>
      <FocusLock group="booking-workflow">
        <AddUser onSuccess={refreshList} />
      </FocusLock>
      <UserTable
        triggerRefresh={triggerRefresh}
        setTriggerRefresh={setTriggerRefresh}
      />
    </div>
  );
};
