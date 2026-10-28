import React, { useEffect } from 'react';
import Navbar from './navbar/Navbar';
import './app.css';
import { BrowserRouter, Route, Switch, Redirect } from 'react-router-dom';
import Registration from './authorization/Registration';
import Login from './authorization/Login';
import { useDispatch, useSelector } from 'react-redux';
import { auth } from '../actions/user';
import Disk from './disk/Disk';
import Profile from './profile/Profile';

function App() {
  const isAuth = useSelector((state) => state.user.isAuth);
  const dispatch = useDispatch();

  useEffect(() => {
    if (localStorage.getItem('token')) {
      dispatch(auth());
    }
  }, []);
  
   useEffect(() => {
    const handleBeforeUnload = (event) => {
      event.preventDefault();
      event.returnValue = '';
      
      const message = 'Вы уверены, что хотите покинуть страницу?';
      event.returnValue = message;
      return message;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <div className="wrap container">
          {!isAuth ? (
            <Switch>
              <Route path="/autmama/registration" component={Registration} />
              <Route path="/autmama/login" component={Login} />
              <Route path="/autmama/privacy" render={() => <Redirect to="/autmama/privacy.html" />} />
              <Redirect to="/autmama/login" />
            </Switch>
          ) : (
            <Switch>
              <Route exact path="/autmama/" component={Disk} />
              <Route exact path="/autmama/profile" component={Profile} />
              <Route path="/autmama/privacy" render={() => <Redirect to="/autmama/privacy.html" />} />
              <Redirect to="/autmama/" />
            </Switch>
          )}
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
