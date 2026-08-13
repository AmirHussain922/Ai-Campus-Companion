import { createBrowserRouter, Navigate, Outlet } from "react-router";
import { useStore } from "./store";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import VerifyEmail from "./pages/VerifyEmail";
import ForgotPassword from "./pages/ForgotPassword";
import CompanionSelection from "./pages/CompanionSelection";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import UserProfile from "./pages/UserProfile";
import SettingsPersonal from "./pages/SettingsPersonal";
import SettingsSecurity from "./pages/SettingsSecurity";
import SettingsNotifications from "./pages/SettingsNotifications";
import SupportHelpCenter from "./pages/SupportHelpCenter";
import SupportContact from "./pages/SupportContact";
import SupportTerms from "./pages/SupportTerms";
import Payment from "./pages/Payment";
import MainLayout from "./layouts/MainLayout";
import AuthLayout from "./layouts/AuthLayout";
import CompanionProfilePage from "./pages/CompanionProfilePage";
import EpisodesListPage from "./pages/EpisodesListPage";
import EpisodePlayer from "./components/EpisodePlayer";
import JournalPage from "./pages/JournalPage";
import StudyBuddyProfileSetup from "./pages/StudyBuddyProfileSetup";
import StudyBuddyMatches from "./pages/StudyBuddyMatches";
import StudyBuddyConnections from "./pages/StudyBuddyConnections";
import StudyBuddyDM from "./pages/StudyBuddyDM";
import PeerQAList from "./pages/PeerQAList";
import QuestionDetail from "./pages/QuestionDetail";
import StudyRoomPage from "./pages/StudyRoomPage";

// Protected Route Component - requires authentication
function ProtectedRoute() {
  const authToken = useStore(state => state.authToken);
  if (!authToken) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Landing />,
  },
  {
    element: <AuthLayout />,
    children: [
      { path: "login", element: <Login /> },
      { path: "signup", element: <Signup /> },
      { path: "verify-email", element: <VerifyEmail /> },
      { path: "forgot-password", element: <ForgotPassword /> },
    ]
  },
  {
    path: "select",
    element: <CompanionSelection />,
  },
  {
    path: "upgrade",
    element: <Payment />,
  },
  {
    path: "app",
    element: <ProtectedRoute />,
    children: [
      { element: <MainLayout />, children: [
        { index: true, element: <Dashboard /> },
        { path: "chat/:id", element: <Chat /> },
        { path: "profile/:id", element: <Navigate to="/app/companion/:id/profile" replace /> }, // Redirect old route
        { path: "companion/:companionId/profile", element: <CompanionProfilePage /> },
        { path: "companion/:companionId/chat", element: <Chat /> },
        { path: "companion/:companionId/episodes", element: <EpisodesListPage /> },
        { path: "companion/:companionId/episodes/play/:episodeId", element: <EpisodePlayer /> },
        { path: "companion/:companionId/journal", element: <JournalPage /> },
        { path: "me", element: <UserProfile /> },
        { path: "study-buddy/profile", element: <StudyBuddyProfileSetup /> },
        { path: "study-buddy/matches", element: <StudyBuddyMatches /> },
        { path: "study-buddy/connections", element: <StudyBuddyConnections /> },
        { path: "study-buddy/dm/:conversationId", element: <StudyBuddyDM /> },
        { path: "qa", element: <PeerQAList /> },
        { path: "qa/:id", element: <QuestionDetail /> },
        { path: "study-rooms", element: <StudyRoomPage /> },
        { path: "settings/personal", element: <SettingsPersonal /> },
        { path: "settings/security", element: <SettingsSecurity /> },
        { path: "settings/notifications", element: <SettingsNotifications /> },
        { path: "support/help", element: <SupportHelpCenter /> },
        { path: "support/contact", element: <SupportContact /> },
        { path: "support/terms", element: <SupportTerms /> },
      ]}
    ]
  },
  {
    path: "*",
    element: <Navigate to="/" replace />
  }
]);
