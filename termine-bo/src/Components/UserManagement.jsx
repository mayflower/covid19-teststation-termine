import React, { useState } from "react";
import FocusLock from "react-focus-lock";
import { AddUser } from "./AddUser";
import { UserTable } from "./UserTable";

export const UserManagement = () => {
  const [triggerRefresh, setTriggerRefresh] = useState(true);
  const refreshList = () => setTriggerRefresh(true);

  return (<>
    <FocusLock group="booking-workflow">
      <AddUser onSuccess={refreshList} />
    </FocusLock>
    <UserTable
      triggerRefresh={triggerRefresh}
      setTriggerRefresh={setTriggerRefresh}
    />
  </>
  );
};
