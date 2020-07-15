using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class ButtonHandler : MonoBehaviour
{
    private void Start()
    {
        Buttons.up_button = false;
        Buttons.right_button = false;
    }

    public void onPress()
    {
        if (name.Contains("Up"))
        {
            Buttons.up_button = true;
        }
        if (name.Contains("Right"))
        {
            Buttons.right_button = true;
        }
    }
    
    public void onRelease()
    {
        if (name.Contains("Up"))
        {
            Buttons.up_button = false;
        }
        if (name.Contains("Right"))
        {
            Buttons.right_button = false;
        }
    }

    
}