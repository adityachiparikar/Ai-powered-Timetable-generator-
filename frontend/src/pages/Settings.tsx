import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Settings() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                <p className="text-muted-foreground">Manage application settings.</p>
            </div>

            <Card className="max-w-xl">
                <CardHeader>
                    <CardTitle>General Settings</CardTitle>
                    <CardDescription>Configure basic application parameters.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Institute Name</Label>
                        <Input defaultValue="My University" />
                    </div>
                    <div className="space-y-2">
                        <Label>Academic Year</Label>
                        <Input defaultValue="2024-2025" />
                    </div>
                    <Button>Save Changes</Button>
                </CardContent>
            </Card>
        </div>
    );
}
