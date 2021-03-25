import React from "react";
import { UserManagement } from "./Components/UserManagement";
import { AppointmentManagement } from "./Components/AppointmentManagement";
import {
  HashRouter as Router,
  Route,
  Link,
  Switch,
  Redirect,
} from "react-router-dom";

const TAB = {
  USER_MANAGEMENT: "/users",
  APPOINTMENT_MANAGEMENT: "/appointments",
};

export const App = () => (
  <div className="container">
    <Router>
      <header style={{ minHeight: "54px", maxHeight: "6vh" }}>
        <div className="displayFlex">
          <h3 style={{ paddingLeft: "var(--universal-padding)" }}>
            {window.config.longInstanceName}
          </h3>
          <Link className="button" to={TAB.USER_MANAGEMENT}>
            Manage Users
          </Link>
          <Link className="button" to={TAB.APPOINTMENT_MANAGEMENT}>
            Manage Appointments
          </Link>
        </div>
      </header>
      <Switch>
        <Route exact path="/">
          <Redirect to={TAB.USER_MANAGEMENT} />
        </Route>
        <Route path={TAB.USER_MANAGEMENT}>
          <UserManagement />
        </Route>
        <Route path={TAB.APPOINTMENT_MANAGEMENT}>
          <AppointmentManagement />
        </Route>
      </Switch>
    </Router>
  </div>
);
