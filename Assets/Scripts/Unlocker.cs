using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class Unlocker : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        if (!Unlocks.initialized)
        {
            for (int i = 0; i < Unlocks.num_levels; i++)
            {
                Unlocks.level_done[i] = false;
            }
            Unlocks.initialized = true;
        }
        for (int i = 1; i < Unlocks.num_levels; i++)
        {
            GameObject level_button_obj = GameObject.Find("Level" + (i + 1) + " Button");
            Button level_button = level_button_obj.GetComponent<Button>();
            level_button.enabled = Unlocks.level_done[i];
            if (!Unlocks.level_done[i])
            {
                level_button_obj.GetComponent<Image>().color = new Color(0.0f, 0.0f, 0.0f);
            }
        }
    }
}

public static class Unlocks
{
    public static bool initialized = false;
    public static int num_levels = 10;
    public static bool[] level_done = new bool[num_levels];
}