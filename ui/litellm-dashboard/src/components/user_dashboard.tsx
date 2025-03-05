"use client";
import React, { useState, useEffect } from "react";
import {
  userInfoCall,
  modelAvailableCall,
  getTotalSpendCall,
  getProxyUISettings,
  Organization,
  organizationListCall,
  DEFAULT_ORGANIZATION
} from "./networking";
import { fetchTeams } from "./common_components/fetch_teams";
import { Grid, Col, Card, Text, Title } from "@tremor/react";
import CreateKey from "./create_key_button";
import ViewKeyTable from "./view_key_table";
import ViewUserSpend from "./view_user_spend";
import ViewUserTeam from "./view_user_team";
import DashboardTeam from "./dashboard_default_team";
import Onboarding from "../app/onboarding/page";
import { useSearchParams, useRouter } from "next/navigation";
import { Team } from "./key_team_helpers/key_list";
import { jwtDecode } from "jwt-decode";
import { Typography } from "antd";
import { getUISessionDetails } from "@/utils/cookieUtils";
import { clearTokenCookies } from "@/utils/cookieUtils";
const isLocal = process.env.NODE_ENV === "development";
if (isLocal != true) {
  console.log = function() {};
}
console.log("isLocal:", isLocal);
const proxyBaseUrl = isLocal ? "http://localhost:4000" : null;

export interface ProxySettings {
  PROXY_BASE_URL: string | null;
  PROXY_LOGOUT_URL: string | null;
  DEFAULT_TEAM_DISABLED: boolean;
  SSO_ENABLED: boolean;
  DISABLE_EXPENSIVE_DB_QUERIES: boolean;
  NUM_SPEND_LOGS_ROWS: number;
}


export type UserInfo = {
  models: string[];
  max_budget?: number | null;
  spend: number;
}

interface UserDashboardProps {
  userID: string | null;
  userRole: string | null;
  userEmail: string | null;
  teams: Team[] | null;
  keys: any[] | null;
  setUserRole: React.Dispatch<React.SetStateAction<string>>;
  setUserEmail: React.Dispatch<React.SetStateAction<string | null>>;
  setTeams: React.Dispatch<React.SetStateAction<Team[] | null>>;
  setKeys: React.Dispatch<React.SetStateAction<Object[] | null>>;
  premiumUser: boolean;
  organizations: Organization[] | null;
}

type TeamInterface = {
  models: any[];
  team_id: null;
  team_alias: String;
};

const UserDashboard: React.FC<UserDashboardProps> = ({
  userID,
  userRole,
  teams,
  keys,
  setUserRole,
  userEmail,
  setUserEmail,
  setTeams,
  setKeys,
  premiumUser,
  organizations
}) => {
  const [userSpendData, setUserSpendData] = useState<UserInfo | null>(
    null
  );
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);

  // Assuming useSearchParams() hook exists and works in your setup
  const searchParams = useSearchParams()!;

  const token = getUISessionDetails();

  const invitation_id = searchParams.get("invitation_id");

  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [teamSpend, setTeamSpend] = useState<number | null>(null);
  const [userModels, setUserModels] = useState<string[]>([]);
  const [proxySettings, setProxySettings] = useState<ProxySettings | null>(null);
  const defaultTeam: TeamInterface = {
    models: [],
    team_alias: "Default Team",
    team_id: null,
  };
  const [selectedTeam, setSelectedTeam] = useState<any | null>(null);
  // check if window is not undefined
  if (typeof window !== "undefined") {
    window.addEventListener("beforeunload", function () {
      // Clear session storage
      sessionStorage.clear();
    });
  }

  function formatUserRole(userRole: string) {
    if (!userRole) {
      return "Undefined Role";
    }
    console.log(`Received user role: ${userRole}`);
    switch (userRole.toLowerCase()) {
      case "app_owner":
        return "App Owner";
      case "demo_app_owner":
        return "App Owner";
      case "app_admin":
        return "Admin";
      case "proxy_admin":
        return "Admin";
      case "proxy_admin_viewer":
        return "Admin Viewer";
      case "app_user":
        return "App User";
      case "internal_user":
        return "Internal User";
      case "internal_user_viewer":
        return "Internal Viewer";
      default:
        return "Unknown Role";
    }
  }

  // console.log(`selectedTeam: ${Object.entries(selectedTeam)}`);
  // Moved useEffect inside the component and used a condition to run fetch only if the params are available
  useEffect(() => {
    const fetchSessionDetails = async () => {
      try {
        const sessionDetails = await getUISessionDetails();
        console.log("Session details:", sessionDetails);
        
        // Set access token to the session_id
        setAccessToken(sessionDetails.session_id);
        
        // check if userRole is defined
        if (sessionDetails.user_role) {
          const formattedUserRole = formatUserRole(sessionDetails.user_role);
          console.log("User role:", formattedUserRole);
          setUserRole(formattedUserRole);
        } else {
          console.log("User role not defined");
        }

        if (sessionDetails.user_email) {
          setUserEmail(sessionDetails.user_email);
        } else {
          console.log("User Email is not set");
        }
      } catch (error) {
        console.error("Error fetching session details:", error);
      }
    };
    
    fetchSessionDetails();
  }, []);

  useEffect(() => {
    if (userID && accessToken && userRole && !keys && !userSpendData) {
      const cachedUserModels = sessionStorage.getItem("userModels" + userID);
      if (cachedUserModels) {
        setUserModels(JSON.parse(cachedUserModels));
      } else {
        console.log(`currentOrg: ${JSON.stringify(currentOrg)}`)
        const fetchData = async () => {
          try {
            const proxy_settings: ProxySettings = await getProxyUISettings(accessToken);
            setProxySettings(proxy_settings);

            const response = await userInfoCall(
              accessToken,
              userID,
              userRole,
              false,
              null,
              null
            );

            setUserSpendData(response["user_info"]);
            console.log(`userSpendData: ${JSON.stringify(userSpendData)}`)
            

            // set keys for admin and users
            if (!response?.teams[0].keys) {
              setKeys(response["keys"]); 
            } else {
              setKeys(
                response["keys"].concat(
                  response.teams
                    .filter((team: any) => userRole === "Admin" || team.user_id === userID)
                    .flatMap((team: any) => team.keys)
                )
              );
              
            }

            sessionStorage.setItem(
              "userData" + userID,
              JSON.stringify(response["keys"])
            );
            sessionStorage.setItem(
              "userSpendData" + userID,
              JSON.stringify(response["user_info"])
            );

            const model_available = await modelAvailableCall(
              accessToken,
              userID,
              userRole
            );
            // loop through model_info["data"] and create an array of element.model_name
            let available_model_names = model_available["data"].map(
              (element: { id: string }) => element.id
            );
            console.log("available_model_names:", available_model_names);
            setUserModels(available_model_names);

            console.log("userModels:", userModels);

            sessionStorage.setItem(
              "userModels" + userID,
              JSON.stringify(available_model_names)
            );
          } catch (error) {
            console.error("There was an error fetching the data", error);
            // Optionally, update your UI to reflect the error state here as well
          }
        };
        fetchData();
        fetchTeams(accessToken, userID, userRole, currentOrg, setTeams);
      }
    }
  }, [userID, accessToken, keys, userRole]);

  useEffect(() => {
    console.log(`currentOrg: ${JSON.stringify(currentOrg)}, accessToken: ${accessToken}, userID: ${userID}, userRole: ${userRole}`)
    if (accessToken) {
      console.log(`fetching teams`)
      fetchTeams(accessToken, userID, userRole, currentOrg, setTeams);
    }
  }, [currentOrg]);

  useEffect(() => {
    // This code will run every time selectedTeam changes
    if (
      keys !== null &&
      selectedTeam !== null &&
      selectedTeam !== undefined &&
      selectedTeam.team_id !== null
    ) {
      let sum = 0;
      console.log(`keys: ${JSON.stringify(keys)}`)
      for (const key of keys) {
        if (
          selectedTeam.hasOwnProperty("team_id") &&
          key.team_id !== null &&
          key.team_id === selectedTeam.team_id
        ) {
          sum += key.spend;
        }
      }
      console.log(`sum: ${sum}`)
      setTeamSpend(sum);
    } else if (keys !== null) {
      // sum the keys which don't have team-id set (default team)
      let sum = 0;
      for (const key of keys) {
        sum += key.spend;
      }
      setTeamSpend(sum);
    }
  }, [selectedTeam]);


  if (invitation_id != null) {
    return (
      <Onboarding></Onboarding>
    )
  }

  if (userID == null || token == null) {
    // user is not logged in as yet 
    console.log("All cookies before redirect:", document.cookie);
    
    // Clear token cookies using the utility function
    clearTokenCookies();
    
    const url = proxyBaseUrl
      ? `${proxyBaseUrl}/sso/key/generate`
      : `/sso/key/generate`;
    
    console.log("Full URL:", url);
    window.location.href = url;

    return null;
  } else if (accessToken == null) {
    return null;
  }

  if (userRole == null) {
    setUserRole("App Owner");
  }

  if (userRole && userRole == "Admin Viewer") {
    const { Title, Paragraph } = Typography;
    return (
      <div>
        <Title level={1}>Access Denied</Title>
        <Paragraph>Ask your proxy admin for access to create keys</Paragraph>
      </div>
    );
  }

  console.log("inside user dashboard, selected team", selectedTeam);
  console.log("All cookies after redirect:", document.cookie);
  return (
    <div className="w-full mx-4 h-[75vh]">
      <Grid numItems={1} className="gap-2 p-8 w-full mt-2">
        <Col numColSpan={1} className="flex flex-col gap-2">
        {accessToken && (
          <>
            <CreateKey
              key={selectedTeam ? selectedTeam.team_id : null}
              userID={userID}
              team={selectedTeam as Team | null}
              teams={teams as Team[]}
              userRole={userRole}
              accessToken={accessToken}
              data={keys}
              setData={setKeys}
            />

            <ViewKeyTable
              userID={userID}
              userRole={userRole}
              accessToken={accessToken}
              selectedTeam={selectedTeam ? selectedTeam : null}
              setSelectedTeam={setSelectedTeam}
              data={keys}
              setData={setKeys}
              premiumUser={premiumUser}
              teams={teams}
              currentOrg={currentOrg}
              setCurrentOrg={setCurrentOrg}
              organizations={organizations}
            />
          </>
        )}
        </Col>
      </Grid>
    </div>
  );
};

export default UserDashboard;
