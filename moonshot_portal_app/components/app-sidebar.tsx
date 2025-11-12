import { Home, History, Network } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

// Menu items.
const items = [
  {
    title: "Home",
    url: "/",
    icon: Home,
    testId: "sidebar-back-to-home-button",
  },
  {
    title: "History",
    url: "/history",
    icon: History,
    testId: "sidebar-history-button",
  },
  {
    title: "Connectors",
    url: "/",
    icon: Network,
    testId: "sidebar-connectors-button",
  },
]

export function AppSidebar() {
  return (
    <Sidebar collapsible="none" className="w-12 border-r h-screen fixed left-0 top-0 z-40">
      <SidebarContent className="h-full">
        <SidebarGroup className="h-full">
          <SidebarGroupContent className="h-full flex items-start">
            <SidebarMenu className="gap-3">
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild tooltip={item.title}>
                    <a href={item.url} data-testid={item.testId}>
                      <item.icon />
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}