// Paste into the Java Shell of an OPEN, authorized COMSOL model.
// Read-only: no set(), solve(), save(), or modification to the loaded model.
// Export only information you have permission to share; keep output local.
// COMSOL 6.4 FeatureInfo.getInfoTable API: Expression, Weak, Constraint, Shape.
// If Equation View is incomplete, first update the model/study in COMSOL UI.
for (String ct : model.component().tags()) {
    for (String pt : model.component(ct).physics().tags()) {
        System.out.println("PHYSICS " + ct + "/" + pt);
        try {
            var info = model.component(ct).physics(pt).featureInfo("info");
            for (String id : new String[]{"Expression","Weak","Constraint","Shape"}) {
                System.out.println("TABLE " + id);
                try {
                    for (String[] row : info.getInfoTable(id,"recursive","all")) {
                        System.out.println(java.util.Arrays.toString(row));
                    }
                } catch (Exception ex) {
                    System.out.println("UNAVAILABLE " + id + ": " + ex.getMessage());
                }
            }
        } catch (Exception ex) {
            System.out.println("UNAVAILABLE " + ct + "/" + pt + ": " + ex.getMessage());
        }
    }
}
