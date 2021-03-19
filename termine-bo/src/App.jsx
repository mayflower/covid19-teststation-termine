import React from "react";
import { UserManagement } from "./Components/UserManagement";
import {
  HashRouter as Router,
  Route,
  NavLink,
  Switch,
  Redirect,
} from "react-router-dom";

export const App = () => (
  <Router>
    <Switch>
      <Route exact path="/">
        <Redirect to="/users" />
      </Route>
      <Route path="/users">
        <UserManagement />
      </Route>
    </Switch>
  </Router>
);
